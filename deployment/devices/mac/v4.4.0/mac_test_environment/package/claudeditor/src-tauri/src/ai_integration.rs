use serde::{Deserialize, Serialize};
use anyhow::{Result, anyhow};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AIRequest {
    pub id: String,
    pub model: String,
    pub prompt: String,
    pub context: Option<String>,
    pub parameters: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AIResponse {
    pub id: String,
    pub model: String,
    pub content: String,
    pub usage: Option<AIUsage>,
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AIUsage {
    pub prompt_tokens: u32,
    pub completion_tokens: u32,
    pub total_tokens: u32,
    pub cost: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AIModel {
    pub id: String,
    pub name: String,
    pub provider: String,
    pub capabilities: Vec<String>,
    pub max_tokens: u32,
    pub cost_per_token: Option<f64>,
}

pub struct AIIntegration {
    models: HashMap<String, AIModel>,
    api_keys: HashMap<String, String>,
}

impl AIIntegration {
    pub fn new() -> Self {
        let mut integration = Self {
            models: HashMap::new(),
            api_keys: HashMap::new(),
        };
        
        integration.initialize_models();
        integration
    }
    
    fn initialize_models(&mut self) {
        // Claude Models
        self.models.insert("claude-3-5-sonnet".to_string(), AIModel {
            id: "claude-3-5-sonnet".to_string(),
            name: "Claude 3.5 Sonnet".to_string(),
            provider: "anthropic".to_string(),
            capabilities: vec![
                "text_generation".to_string(),
                "code_generation".to_string(),
                "analysis".to_string(),
                "reasoning".to_string(),
            ],
            max_tokens: 200000,
            cost_per_token: Some(0.000003),
        });
        
        self.models.insert("claude-3-haiku".to_string(), AIModel {
            id: "claude-3-haiku".to_string(),
            name: "Claude 3 Haiku".to_string(),
            provider: "anthropic".to_string(),
            capabilities: vec![
                "text_generation".to_string(),
                "code_generation".to_string(),
                "fast_response".to_string(),
            ],
            max_tokens: 200000,
            cost_per_token: Some(0.00000025),
        });
        
        // OpenAI Models
        self.models.insert("gpt-4".to_string(), AIModel {
            id: "gpt-4".to_string(),
            name: "GPT-4".to_string(),
            provider: "openai".to_string(),
            capabilities: vec![
                "text_generation".to_string(),
                "code_generation".to_string(),
                "function_calling".to_string(),
                "vision".to_string(),
            ],
            max_tokens: 128000,
            cost_per_token: Some(0.00003),
        });
        
        self.models.insert("gpt-3.5-turbo".to_string(), AIModel {
            id: "gpt-3.5-turbo".to_string(),
            name: "GPT-3.5 Turbo".to_string(),
            provider: "openai".to_string(),
            capabilities: vec![
                "text_generation".to_string(),
                "code_generation".to_string(),
                "function_calling".to_string(),
            ],
            max_tokens: 16385,
            cost_per_token: Some(0.0000015),
        });
        
        // Google Models
        self.models.insert("gemini-pro".to_string(), AIModel {
            id: "gemini-pro".to_string(),
            name: "Gemini Pro".to_string(),
            provider: "google".to_string(),
            capabilities: vec![
                "text_generation".to_string(),
                "code_generation".to_string(),
                "multimodal".to_string(),
            ],
            max_tokens: 32768,
            cost_per_token: Some(0.000001),
        });
    }
    
    pub fn get_available_models(&self) -> Vec<&AIModel> {
        self.models.values().collect()
    }
    
    pub fn get_model(&self, model_id: &str) -> Option<&AIModel> {
        self.models.get(model_id)
    }
    
    pub fn set_api_key(&mut self, provider: &str, api_key: String) {
        self.api_keys.insert(provider.to_string(), api_key);
    }
    
    pub async fn generate_text(&self, request: AIRequest) -> Result<AIResponse> {
        log::info!("Generating text with model: {}", request.model);
        
        let model = self.models.get(&request.model)
            .ok_or_else(|| anyhow!("Model '{}' not found", request.model))?;
        
        let api_key = self.api_keys.get(&model.provider)
            .ok_or_else(|| anyhow!("API key not found for provider '{}'", model.provider))?;
        
        match model.provider.as_str() {
            "anthropic" => self.call_anthropic_api(&request, api_key).await,
            "openai" => self.call_openai_api(&request, api_key).await,
            "google" => self.call_google_api(&request, api_key).await,
            _ => Err(anyhow!("Unsupported provider: {}", model.provider)),
        }
    }
    
    async fn call_anthropic_api(&self, request: &AIRequest, api_key: &str) -> Result<AIResponse> {
        log::info!("Calling Anthropic API for model: {}", request.model);
        
        let client = reqwest::Client::new();
        
        let payload = serde_json::json!({
            "model": request.model,
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": request.prompt
                }
            ]
        });
        
        let response = client
            .post("https://api.anthropic.com/v1/messages")
            .header("Content-Type", "application/json")
            .header("x-api-key", api_key)
            .header("anthropic-version", "2023-06-01")
            .json(&payload)
            .send()
            .await
            .map_err(|e| anyhow!("Failed to call Anthropic API: {}", e))?;
        
        if !response.status().is_success() {
            let error_text = response.text().await.unwrap_or_default();
            return Err(anyhow!("Anthropic API error: {}", error_text));
        }
        
        let response_data: serde_json::Value = response.json().await
            .map_err(|e| anyhow!("Failed to parse Anthropic response: {}", e))?;
        
        let content = response_data["content"][0]["text"]
            .as_str()
            .unwrap_or("")
            .to_string();
        
        let usage = if let Some(usage_data) = response_data.get("usage") {
            Some(AIUsage {
                prompt_tokens: usage_data["input_tokens"].as_u64().unwrap_or(0) as u32,
                completion_tokens: usage_data["output_tokens"].as_u64().unwrap_or(0) as u32,
                total_tokens: (usage_data["input_tokens"].as_u64().unwrap_or(0) + 
                              usage_data["output_tokens"].as_u64().unwrap_or(0)) as u32,
                cost: None, // Calculate based on model pricing
            })
        } else {
            None
        };
        
        Ok(AIResponse {
            id: request.id.clone(),
            model: request.model.clone(),
            content,
            usage,
            metadata: HashMap::new(),
        })
    }
    
    async fn call_openai_api(&self, request: &AIRequest, api_key: &str) -> Result<AIResponse> {
        log::info!("Calling OpenAI API for model: {}", request.model);
        
        let client = reqwest::Client::new();
        
        let payload = serde_json::json!({
            "model": request.model,
            "messages": [
                {
                    "role": "user",
                    "content": request.prompt
                }
            ],
            "max_tokens": 4096
        });
        
        let response = client
            .post("https://api.openai.com/v1/chat/completions")
            .header("Content-Type", "application/json")
            .header("Authorization", format!("Bearer {}", api_key))
            .json(&payload)
            .send()
            .await
            .map_err(|e| anyhow!("Failed to call OpenAI API: {}", e))?;
        
        if !response.status().is_success() {
            let error_text = response.text().await.unwrap_or_default();
            return Err(anyhow!("OpenAI API error: {}", error_text));
        }
        
        let response_data: serde_json::Value = response.json().await
            .map_err(|e| anyhow!("Failed to parse OpenAI response: {}", e))?;
        
        let content = response_data["choices"][0]["message"]["content"]
            .as_str()
            .unwrap_or("")
            .to_string();
        
        let usage = if let Some(usage_data) = response_data.get("usage") {
            Some(AIUsage {
                prompt_tokens: usage_data["prompt_tokens"].as_u64().unwrap_or(0) as u32,
                completion_tokens: usage_data["completion_tokens"].as_u64().unwrap_or(0) as u32,
                total_tokens: usage_data["total_tokens"].as_u64().unwrap_or(0) as u32,
                cost: None, // Calculate based on model pricing
            })
        } else {
            None
        };
        
        Ok(AIResponse {
            id: request.id.clone(),
            model: request.model.clone(),
            content,
            usage,
            metadata: HashMap::new(),
        })
    }
    
    async fn call_google_api(&self, request: &AIRequest, api_key: &str) -> Result<AIResponse> {
        log::info!("Calling Google API for model: {}", request.model);
        
        // Placeholder for Google Gemini API integration
        // This would implement the actual Google AI API calls
        
        Ok(AIResponse {
            id: request.id.clone(),
            model: request.model.clone(),
            content: format!("Google Gemini response to: {}", request.prompt),
            usage: Some(AIUsage {
                prompt_tokens: 100,
                completion_tokens: 200,
                total_tokens: 300,
                cost: Some(0.0003),
            }),
            metadata: HashMap::new(),
        })
    }
    
    pub async fn generate_code(&self, language: &str, description: &str, model: Option<&str>) -> Result<String> {
        let model_id = model.unwrap_or("claude-3-5-sonnet");
        
        let prompt = format!(
            "Generate {} code for the following description:\n\n{}\n\nPlease provide clean, well-commented code with proper error handling.",
            language, description
        );
        
        let request = AIRequest {
            id: uuid::Uuid::new_v4().to_string(),
            model: model_id.to_string(),
            prompt,
            context: None,
            parameters: HashMap::new(),
        };
        
        let response = self.generate_text(request).await?;
        Ok(response.content)
    }
    
    pub async fn analyze_code(&self, code: &str, language: &str, model: Option<&str>) -> Result<String> {
        let model_id = model.unwrap_or("claude-3-5-sonnet");
        
        let prompt = format!(
            "Analyze the following {} code and provide feedback on:\n\
            1. Code quality and best practices\n\
            2. Potential bugs or issues\n\
            3. Performance improvements\n\
            4. Security considerations\n\n\
            Code:\n```{}\n{}\n```",
            language, language, code
        );
        
        let request = AIRequest {
            id: uuid::Uuid::new_v4().to_string(),
            model: model_id.to_string(),
            prompt,
            context: None,
            parameters: HashMap::new(),
        };
        
        let response = self.generate_text(request).await?;
        Ok(response.content)
    }
    
    pub async fn explain_code(&self, code: &str, language: &str, model: Option<&str>) -> Result<String> {
        let model_id = model.unwrap_or("claude-3-5-sonnet");
        
        let prompt = format!(
            "Explain the following {} code in detail:\n\n\
            ```{}\n{}\n```\n\n\
            Please provide:\n\
            1. Overall purpose and functionality\n\
            2. Step-by-step explanation of key parts\n\
            3. Any important concepts or patterns used",
            language, language, code
        );
        
        let request = AIRequest {
            id: uuid::Uuid::new_v4().to_string(),
            model: model_id.to_string(),
            prompt,
            context: None,
            parameters: HashMap::new(),
        };
        
        let response = self.generate_text(request).await?;
        Ok(response.content)
    }
    
    pub fn calculate_cost(&self, model_id: &str, tokens: u32) -> Option<f64> {
        if let Some(model) = self.models.get(model_id) {
            model.cost_per_token.map(|cost| cost * tokens as f64)
        } else {
            None
        }
    }
}

