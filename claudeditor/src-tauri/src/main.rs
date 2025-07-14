// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::collections::HashMap;
use std::sync::Mutex;
use tauri::{Manager, State};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};

// PowerAutomation MCP Integration
mod mcp;
mod powerautomation;
mod file_manager;
mod project_manager;
mod ai_integration;

use mcp::MCPCoordinator;
use powerautomation::PowerAutomationCore;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Project {
    pub id: String,
    pub name: String,
    pub path: String,
    pub created_at: DateTime<Utc>,
    pub last_modified: DateTime<Utc>,
    pub description: Option<String>,
    pub tags: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct MCPService {
    pub id: String,
    pub name: String,
    pub url: String,
    pub status: String,
    pub capabilities: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AIAgent {
    pub id: String,
    pub name: String,
    pub agent_type: String,
    pub status: String,
    pub capabilities: Vec<String>,
}

// Application State
#[derive(Default)]
pub struct AppState {
    pub projects: Mutex<HashMap<String, Project>>,
    pub mcp_services: Mutex<HashMap<String, MCPService>>,
    pub ai_agents: Mutex<HashMap<String, AIAgent>>,
    pub mcp_coordinator: Mutex<Option<MCPCoordinator>>,
    pub powerautomation_core: Mutex<Option<PowerAutomationCore>>,
}

// Tauri Commands
#[tauri::command]
async fn initialize_powerautomation(state: State<'_, AppState>) -> Result<String, String> {
    log::info!("Initializing PowerAutomation core...");
    
    // Initialize components first to avoid holding locks across awaits
    let core = PowerAutomationCore::new().await.map_err(|e| e.to_string())?;
    let coordinator = MCPCoordinator::new().await.map_err(|e| e.to_string())?;
    
    // Then update state
    {
        let mut core_guard = state.powerautomation_core.lock().unwrap();
        *core_guard = Some(core);
    }
    
    {
        let mut mcp_guard = state.mcp_coordinator.lock().unwrap();
        *mcp_guard = Some(coordinator);
    }
    
    log::info!("PowerAutomation core initialized successfully");
    Ok("PowerAutomation initialized successfully".to_string())
}

#[tauri::command]
async fn create_project(
    name: String,
    path: String,
    description: Option<String>,
    state: State<'_, AppState>
) -> Result<Project, String> {
    log::info!("Creating new project: {}", name);
    
    let project = Project {
        id: Uuid::new_v4().to_string(),
        name: name.clone(),
        path: path.clone(),
        created_at: Utc::now(),
        last_modified: Utc::now(),
        description,
        tags: vec![],
    };
    
    let mut projects = state.projects.lock().unwrap();
    projects.insert(project.id.clone(), project.clone());
    
    // Create project directory if it doesn't exist
    if let Err(e) = std::fs::create_dir_all(&path) {
        log::error!("Failed to create project directory: {}", e);
        return Err(format!("Failed to create project directory: {}", e));
    }
    
    log::info!("Project created successfully: {}", project.id);
    Ok(project)
}

#[tauri::command]
async fn get_projects(state: State<'_, AppState>) -> Result<Vec<Project>, String> {
    let projects = state.projects.lock().unwrap();
    Ok(projects.values().cloned().collect())
}

#[tauri::command]
async fn get_mcp_services(state: State<'_, AppState>) -> Result<Vec<MCPService>, String> {
    let services = state.mcp_services.lock().unwrap();
    Ok(services.values().cloned().collect())
}

#[tauri::command]
async fn discover_mcp_tools(state: State<'_, AppState>) -> Result<Vec<String>, String> {
    log::info!("Discovering MCP tools...");
    
    // Clone the coordinator to avoid holding the lock across await
    let coordinator = {
        let mcp_guard = state.mcp_coordinator.lock().unwrap();
        mcp_guard.as_ref().cloned()
    };
    
    if let Some(coord) = coordinator {
        coord.discover_tools().await.map_err(|e| e.to_string())
    } else {
        Err("MCP Coordinator not initialized".to_string())
    }
}

#[tauri::command]
async fn get_ai_agents(state: State<'_, AppState>) -> Result<Vec<AIAgent>, String> {
    let agents = state.ai_agents.lock().unwrap();
    Ok(agents.values().cloned().collect())
}

#[tauri::command]
async fn read_file_content(file_path: String) -> Result<String, String> {
    log::info!("Reading file: {}", file_path);
    
    std::fs::read_to_string(&file_path)
        .map_err(|e| format!("Failed to read file {}: {}", file_path, e))
}

#[tauri::command]
async fn write_file_content(file_path: String, content: String) -> Result<(), String> {
    log::info!("Writing file: {}", file_path);
    
    // Create parent directories if they don't exist
    if let Some(parent) = std::path::Path::new(&file_path).parent() {
        std::fs::create_dir_all(parent)
            .map_err(|e| format!("Failed to create directories: {}", e))?;
    }
    
    std::fs::write(&file_path, content)
        .map_err(|e| format!("Failed to write file {}: {}", file_path, e))
}

#[tauri::command]
async fn list_directory(dir_path: String) -> Result<Vec<String>, String> {
    log::info!("Listing directory: {}", dir_path);
    
    let entries = std::fs::read_dir(&dir_path)
        .map_err(|e| format!("Failed to read directory {}: {}", dir_path, e))?;
    
    let mut files = Vec::new();
    for entry in entries {
        if let Ok(entry) = entry {
            if let Some(name) = entry.file_name().to_str() {
                files.push(name.to_string());
            }
        }
    }
    
    files.sort();
    Ok(files)
}

#[tauri::command]
async fn get_app_version() -> Result<String, String> {
    Ok(env!("CARGO_PKG_VERSION").to_string())
}

fn main() {
    env_logger::init();
    log::info!("Starting ClaudEditor...");
    
    tauri::Builder::default()
        .manage(AppState::default())
        .invoke_handler(tauri::generate_handler![
            initialize_powerautomation,
            create_project,
            get_projects,
            get_mcp_services,
            discover_mcp_tools,
            get_ai_agents,
            read_file_content,
            write_file_content,
            list_directory,
            get_app_version
        ])
        .setup(|app| {
            log::info!("ClaudEditor setup completed");
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

