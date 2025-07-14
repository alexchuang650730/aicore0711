use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use anyhow::{Result, anyhow};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Project {
    pub id: String,
    pub name: String,
    pub path: String,
    pub description: Option<String>,
    pub created_at: DateTime<Utc>,
    pub last_modified: DateTime<Utc>,
    pub tags: Vec<String>,
    pub settings: ProjectSettings,
    pub files: Vec<ProjectFile>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectSettings {
    pub language: Option<String>,
    pub framework: Option<String>,
    pub ai_model_preference: Option<String>,
    pub auto_save: bool,
    pub git_integration: bool,
    pub mcp_tools: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectFile {
    pub path: String,
    pub name: String,
    pub file_type: String,
    pub size: u64,
    pub last_modified: DateTime<Utc>,
    pub is_open: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectTemplate {
    pub id: String,
    pub name: String,
    pub description: String,
    pub language: String,
    pub framework: Option<String>,
    pub files: Vec<TemplateFile>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TemplateFile {
    pub path: String,
    pub content: String,
    pub is_template: bool,
}

pub struct ProjectManager {
    projects: HashMap<String, Project>,
    templates: HashMap<String, ProjectTemplate>,
}

impl ProjectManager {
    pub fn new() -> Self {
        let mut manager = Self {
            projects: HashMap::new(),
            templates: HashMap::new(),
        };
        
        manager.initialize_templates();
        manager
    }
    
    fn initialize_templates(&mut self) {
        // React TypeScript Template
        self.templates.insert("react_typescript".to_string(), ProjectTemplate {
            id: "react_typescript".to_string(),
            name: "React TypeScript".to_string(),
            description: "Modern React application with TypeScript".to_string(),
            language: "typescript".to_string(),
            framework: Some("react".to_string()),
            files: vec![
                TemplateFile {
                    path: "package.json".to_string(),
                    content: r#"{
  "name": "{{project_name}}",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^4.9.5"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }
}"#.to_string(),
                    is_template: true,
                },
                TemplateFile {
                    path: "src/App.tsx".to_string(),
                    content: r#"import React from 'react';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>{{project_name}}</h1>
        <p>Welcome to your new React TypeScript project!</p>
      </header>
    </div>
  );
}

export default App;"#.to_string(),
                    is_template: true,
                },
            ],
        });
        
        // Python Template
        self.templates.insert("python".to_string(), ProjectTemplate {
            id: "python".to_string(),
            name: "Python Project".to_string(),
            description: "Basic Python project structure".to_string(),
            language: "python".to_string(),
            framework: None,
            files: vec![
                TemplateFile {
                    path: "main.py".to_string(),
                    content: r#"#!/usr/bin/env python3
"""
{{project_name}}
{{description}}
"""

def main():
    print("Hello from {{project_name}}!")

if __name__ == "__main__":
    main()
"#.to_string(),
                    is_template: true,
                },
                TemplateFile {
                    path: "requirements.txt".to_string(),
                    content: "# Add your dependencies here\n".to_string(),
                    is_template: false,
                },
                TemplateFile {
                    path: "README.md".to_string(),
                    content: r#"# {{project_name}}

{{description}}

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```
"#.to_string(),
                    is_template: true,
                },
            ],
        });
        
        // Node.js Template
        self.templates.insert("nodejs".to_string(), ProjectTemplate {
            id: "nodejs".to_string(),
            name: "Node.js Project".to_string(),
            description: "Basic Node.js project with Express".to_string(),
            language: "javascript".to_string(),
            framework: Some("express".to_string()),
            files: vec![
                TemplateFile {
                    path: "package.json".to_string(),
                    content: r#"{
  "name": "{{project_name}}",
  "version": "1.0.0",
  "description": "{{description}}",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "dev": "nodemon index.js"
  },
  "dependencies": {
    "express": "^4.18.2"
  },
  "devDependencies": {
    "nodemon": "^2.0.22"
  }
}"#.to_string(),
                    is_template: true,
                },
                TemplateFile {
                    path: "index.js".to_string(),
                    content: r#"const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());

app.get('/', (req, res) => {
  res.json({ message: 'Hello from {{project_name}}!' });
});

app.listen(port, () => {
  console.log(`{{project_name}} server running on port ${port}`);
});
"#.to_string(),
                    is_template: true,
                },
            ],
        });
    }
    
    pub fn create_project(&mut self, name: String, path: String, description: Option<String>, template_id: Option<String>) -> Result<Project> {
        log::info!("Creating project '{}' at '{}'", name, path);
        
        // Check if project already exists
        if self.projects.values().any(|p| p.path == path) {
            return Err(anyhow!("Project already exists at path '{}'", path));
        }
        
        // Create project directory
        std::fs::create_dir_all(&path)
            .map_err(|e| anyhow!("Failed to create project directory: {}", e))?;
        
        let project = Project {
            id: Uuid::new_v4().to_string(),
            name: name.clone(),
            path: path.clone(),
            description: description.clone(),
            created_at: Utc::now(),
            last_modified: Utc::now(),
            tags: vec![],
            settings: ProjectSettings {
                language: None,
                framework: None,
                ai_model_preference: Some("claude-3-5-sonnet".to_string()),
                auto_save: true,
                git_integration: false,
                mcp_tools: vec![],
            },
            files: vec![],
        };
        
        // Apply template if specified
        if let Some(template_id) = template_id {
            self.apply_template(&project, &template_id)?;
        }
        
        // Save project
        self.projects.insert(project.id.clone(), project.clone());
        self.save_project_metadata(&project)?;
        
        log::info!("Project '{}' created successfully", project.id);
        Ok(project)
    }
    
    fn apply_template(&self, project: &Project, template_id: &str) -> Result<()> {
        log::info!("Applying template '{}' to project '{}'", template_id, project.name);
        
        let template = self.templates.get(template_id)
            .ok_or_else(|| anyhow!("Template '{}' not found", template_id))?;
        
        for template_file in &template.files {
            let file_path = Path::new(&project.path).join(&template_file.path);
            
            // Create parent directories
            if let Some(parent) = file_path.parent() {
                std::fs::create_dir_all(parent)
                    .map_err(|e| anyhow!("Failed to create directories: {}", e))?;
            }
            
            // Process template content
            let content = if template_file.is_template {
                template_file.content
                    .replace("{{project_name}}", &project.name)
                    .replace("{{description}}", &project.description.as_deref().unwrap_or(""))
            } else {
                template_file.content.clone()
            };
            
            // Write file
            std::fs::write(&file_path, content)
                .map_err(|e| anyhow!("Failed to write template file '{}': {}", file_path.display(), e))?;
        }
        
        Ok(())
    }
    
    pub fn get_project(&self, project_id: &str) -> Option<&Project> {
        self.projects.get(project_id)
    }
    
    pub fn get_projects(&self) -> Vec<&Project> {
        self.projects.values().collect()
    }
    
    pub fn update_project(&mut self, project_id: &str, updates: ProjectUpdates) -> Result<()> {
        log::info!("Updating project '{}'", project_id);
        
        let project = self.projects.get_mut(project_id)
            .ok_or_else(|| anyhow!("Project '{}' not found", project_id))?;
        
        if let Some(name) = updates.name {
            project.name = name;
        }
        
        if let Some(description) = updates.description {
            project.description = Some(description);
        }
        
        if let Some(tags) = updates.tags {
            project.tags = tags;
        }
        
        if let Some(settings) = updates.settings {
            project.settings = settings;
        }
        
        project.last_modified = Utc::now();
        
        // Clone project data for metadata saving to avoid borrowing issues  
        let project_clone = project.clone();
        
        // Save updated metadata
        self.save_project_metadata(&project_clone)?;
        
        Ok(())
    }
    
    pub fn delete_project(&mut self, project_id: &str) -> Result<()> {
        log::info!("Deleting project '{}'", project_id);
        
        let project = self.projects.remove(project_id)
            .ok_or_else(|| anyhow!("Project '{}' not found", project_id))?;
        
        // Remove project metadata file
        let metadata_path = Path::new(&project.path).join(".claudeditor").join("project.json");
        if metadata_path.exists() {
            std::fs::remove_file(metadata_path)
                .map_err(|e| anyhow!("Failed to remove project metadata: {}", e))?;
        }
        
        Ok(())
    }
    
    pub fn scan_project_files(&mut self, project_id: &str) -> Result<()> {
        log::info!("Scanning files for project '{}'", project_id);
        
        let project = self.projects.get_mut(project_id)
            .ok_or_else(|| anyhow!("Project '{}' not found", project_id))?;
        
        let mut files = Vec::new();
        
        for entry in walkdir::WalkDir::new(&project.path).max_depth(10) {
            let entry = entry.map_err(|e| anyhow!("Walk error: {}", e))?;
            let path = entry.path();
            
            // Skip directories and hidden files
            if path.is_dir() || path.file_name().unwrap_or_default().to_string_lossy().starts_with('.') {
                continue;
            }
            
            let metadata = path.metadata()
                .map_err(|e| anyhow!("Failed to read metadata: {}", e))?;
            
            let relative_path = path.strip_prefix(&project.path)
                .map_err(|e| anyhow!("Failed to get relative path: {}", e))?;
            
            let file = ProjectFile {
                path: relative_path.to_string_lossy().to_string(),
                name: path.file_name().unwrap_or_default().to_string_lossy().to_string(),
                file_type: path.extension()
                    .map(|ext| ext.to_string_lossy().to_string())
                    .unwrap_or_else(|| "unknown".to_string()),
                size: metadata.len(),
                last_modified: metadata.modified()
                    .map_err(|e| anyhow!("Failed to get modification time: {}", e))?
                    .into(),
                is_open: false,
            };
            
            files.push(file);
        }
        
        project.files = files;
        project.last_modified = Utc::now();
        
        // Clone project data for metadata saving to avoid borrowing issues  
        let project_clone = project.clone();
        
        // Save updated metadata
        self.save_project_metadata(&project_clone)?;
        
        // Get file count and project name for logging
        let file_count = project_clone.files.len();
        let project_name = project_clone.name.clone();
        
        log::info!("Scanned {} files for project '{}'", file_count, project_name);
        Ok(())
    }
    
    pub fn get_templates(&self) -> Vec<&ProjectTemplate> {
        self.templates.values().collect()
    }
    
    fn save_project_metadata(&self, project: &Project) -> Result<()> {
        let metadata_dir = Path::new(&project.path).join(".claudeditor");
        std::fs::create_dir_all(&metadata_dir)
            .map_err(|e| anyhow!("Failed to create metadata directory: {}", e))?;
        
        let metadata_path = metadata_dir.join("project.json");
        let metadata_json = serde_json::to_string_pretty(project)
            .map_err(|e| anyhow!("Failed to serialize project metadata: {}", e))?;
        
        std::fs::write(metadata_path, metadata_json)
            .map_err(|e| anyhow!("Failed to write project metadata: {}", e))?;
        
        Ok(())
    }
    
    pub fn load_project_from_path(&mut self, path: &str) -> Result<Project> {
        log::info!("Loading project from path: {}", path);
        
        let metadata_path = Path::new(path).join(".claudeditor").join("project.json");
        
        if metadata_path.exists() {
            let metadata_content = std::fs::read_to_string(metadata_path)
                .map_err(|e| anyhow!("Failed to read project metadata: {}", e))?;
            
            let mut project: Project = serde_json::from_str(&metadata_content)
                .map_err(|e| anyhow!("Failed to parse project metadata: {}", e))?;
            
            // Update path in case it was moved
            project.path = path.to_string();
            
            // Scan files
            self.projects.insert(project.id.clone(), project.clone());
            self.scan_project_files(&project.id)?;
            
            Ok(self.projects[&project.id].clone())
        } else {
            // Create new project from existing directory
            let name = Path::new(path)
                .file_name()
                .unwrap_or_default()
                .to_string_lossy()
                .to_string();
            
            self.create_project(name, path.to_string(), None, None)
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ProjectUpdates {
    pub name: Option<String>,
    pub description: Option<String>,
    pub tags: Option<Vec<String>>,
    pub settings: Option<ProjectSettings>,
}

