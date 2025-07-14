use std::path::{Path, PathBuf};
use serde::{Deserialize, Serialize};
use anyhow::{Result, anyhow};
use walkdir::WalkDir;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileInfo {
    pub path: String,
    pub name: String,
    pub size: u64,
    pub is_directory: bool,
    pub extension: Option<String>,
    pub modified: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DirectoryTree {
    pub path: String,
    pub name: String,
    pub is_directory: bool,
    pub children: Vec<DirectoryTree>,
}

pub struct FileManager;

impl FileManager {
    pub fn new() -> Self {
        Self
    }
    
    pub fn read_file(&self, file_path: &str) -> Result<String> {
        log::info!("Reading file: {}", file_path);
        
        let content = std::fs::read_to_string(file_path)
            .map_err(|e| anyhow!("Failed to read file '{}': {}", file_path, e))?;
        
        Ok(content)
    }
    
    pub fn write_file(&self, file_path: &str, content: &str) -> Result<()> {
        log::info!("Writing file: {}", file_path);
        
        // Create parent directories if they don't exist
        if let Some(parent) = Path::new(file_path).parent() {
            std::fs::create_dir_all(parent)
                .map_err(|e| anyhow!("Failed to create directories: {}", e))?;
        }
        
        std::fs::write(file_path, content)
            .map_err(|e| anyhow!("Failed to write file '{}': {}", file_path, e))?;
        
        Ok(())
    }
    
    pub fn list_directory(&self, dir_path: &str) -> Result<Vec<FileInfo>> {
        log::info!("Listing directory: {}", dir_path);
        
        let entries = std::fs::read_dir(dir_path)
            .map_err(|e| anyhow!("Failed to read directory '{}': {}", dir_path, e))?;
        
        let mut files = Vec::new();
        
        for entry in entries {
            let entry = entry.map_err(|e| anyhow!("Failed to read directory entry: {}", e))?;
            let path = entry.path();
            let metadata = entry.metadata()
                .map_err(|e| anyhow!("Failed to read metadata: {}", e))?;
            
            let file_info = FileInfo {
                path: path.to_string_lossy().to_string(),
                name: path.file_name()
                    .unwrap_or_default()
                    .to_string_lossy()
                    .to_string(),
                size: metadata.len(),
                is_directory: metadata.is_dir(),
                extension: path.extension()
                    .map(|ext| ext.to_string_lossy().to_string()),
                modified: metadata.modified()
                    .ok()
                    .and_then(|time| time.duration_since(std::time::UNIX_EPOCH).ok())
                    .map(|duration| duration.as_secs().to_string()),
            };
            
            files.push(file_info);
        }
        
        // Sort by name
        files.sort_by(|a, b| a.name.cmp(&b.name));
        
        Ok(files)
    }
    
    pub fn get_directory_tree(&self, dir_path: &str, max_depth: Option<usize>) -> Result<DirectoryTree> {
        log::info!("Building directory tree for: {}", dir_path);
        
        let path = Path::new(dir_path);
        if !path.exists() {
            return Err(anyhow!("Directory '{}' does not exist", dir_path));
        }
        
        self.build_tree_recursive(path, max_depth.unwrap_or(5), 0)
    }
    
    fn build_tree_recursive(&self, path: &Path, max_depth: usize, current_depth: usize) -> Result<DirectoryTree> {
        let metadata = path.metadata()
            .map_err(|e| anyhow!("Failed to read metadata for '{}': {}", path.display(), e))?;
        
        let mut tree = DirectoryTree {
            path: path.to_string_lossy().to_string(),
            name: path.file_name()
                .unwrap_or_default()
                .to_string_lossy()
                .to_string(),
            is_directory: metadata.is_dir(),
            children: Vec::new(),
        };
        
        if metadata.is_dir() && current_depth < max_depth {
            if let Ok(entries) = std::fs::read_dir(path) {
                for entry in entries {
                    if let Ok(entry) = entry {
                        let child_path = entry.path();
                        
                        // Skip hidden files and directories
                        if let Some(name) = child_path.file_name() {
                            if name.to_string_lossy().starts_with('.') {
                                continue;
                            }
                        }
                        
                        if let Ok(child_tree) = self.build_tree_recursive(&child_path, max_depth, current_depth + 1) {
                            tree.children.push(child_tree);
                        }
                    }
                }
                
                // Sort children by name
                tree.children.sort_by(|a, b| a.name.cmp(&b.name));
            }
        }
        
        Ok(tree)
    }
    
    pub fn create_directory(&self, dir_path: &str) -> Result<()> {
        log::info!("Creating directory: {}", dir_path);
        
        std::fs::create_dir_all(dir_path)
            .map_err(|e| anyhow!("Failed to create directory '{}': {}", dir_path, e))?;
        
        Ok(())
    }
    
    pub fn delete_file(&self, file_path: &str) -> Result<()> {
        log::info!("Deleting file: {}", file_path);
        
        let path = Path::new(file_path);
        
        if path.is_dir() {
            std::fs::remove_dir_all(file_path)
                .map_err(|e| anyhow!("Failed to delete directory '{}': {}", file_path, e))?;
        } else {
            std::fs::remove_file(file_path)
                .map_err(|e| anyhow!("Failed to delete file '{}': {}", file_path, e))?;
        }
        
        Ok(())
    }
    
    pub fn copy_file(&self, source: &str, destination: &str) -> Result<()> {
        log::info!("Copying file: {} -> {}", source, destination);
        
        // Create parent directories if they don't exist
        if let Some(parent) = Path::new(destination).parent() {
            std::fs::create_dir_all(parent)
                .map_err(|e| anyhow!("Failed to create directories: {}", e))?;
        }
        
        std::fs::copy(source, destination)
            .map_err(|e| anyhow!("Failed to copy file '{}' to '{}': {}", source, destination, e))?;
        
        Ok(())
    }
    
    pub fn move_file(&self, source: &str, destination: &str) -> Result<()> {
        log::info!("Moving file: {} -> {}", source, destination);
        
        // Create parent directories if they don't exist
        if let Some(parent) = Path::new(destination).parent() {
            std::fs::create_dir_all(parent)
                .map_err(|e| anyhow!("Failed to create directories: {}", e))?;
        }
        
        std::fs::rename(source, destination)
            .map_err(|e| anyhow!("Failed to move file '{}' to '{}': {}", source, destination, e))?;
        
        Ok(())
    }
    
    pub fn search_files(&self, dir_path: &str, pattern: &str, max_results: Option<usize>) -> Result<Vec<FileInfo>> {
        log::info!("Searching files in '{}' with pattern '{}'", dir_path, pattern);
        
        let mut results = Vec::new();
        let max = max_results.unwrap_or(100);
        
        for entry in WalkDir::new(dir_path).max_depth(10) {
            if results.len() >= max {
                break;
            }
            
            let entry = entry.map_err(|e| anyhow!("Walk error: {}", e))?;
            let path = entry.path();
            
            // Skip directories for file search
            if path.is_dir() {
                continue;
            }
            
            // Check if filename matches pattern
            if let Some(filename) = path.file_name() {
                let filename_str = filename.to_string_lossy().to_lowercase();
                let pattern_lower = pattern.to_lowercase();
                
                if filename_str.contains(&pattern_lower) {
                    let metadata = path.metadata()
                        .map_err(|e| anyhow!("Failed to read metadata: {}", e))?;
                    
                    let file_info = FileInfo {
                        path: path.to_string_lossy().to_string(),
                        name: filename.to_string_lossy().to_string(),
                        size: metadata.len(),
                        is_directory: false,
                        extension: path.extension()
                            .map(|ext| ext.to_string_lossy().to_string()),
                        modified: metadata.modified()
                            .ok()
                            .and_then(|time| time.duration_since(std::time::UNIX_EPOCH).ok())
                            .map(|duration| duration.as_secs().to_string()),
                    };
                    
                    results.push(file_info);
                }
            }
        }
        
        log::info!("Found {} files matching pattern '{}'", results.len(), pattern);
        Ok(results)
    }
    
    pub fn get_file_info(&self, file_path: &str) -> Result<FileInfo> {
        let path = Path::new(file_path);
        let metadata = path.metadata()
            .map_err(|e| anyhow!("Failed to read metadata for '{}': {}", file_path, e))?;
        
        let file_info = FileInfo {
            path: file_path.to_string(),
            name: path.file_name()
                .unwrap_or_default()
                .to_string_lossy()
                .to_string(),
            size: metadata.len(),
            is_directory: metadata.is_dir(),
            extension: path.extension()
                .map(|ext| ext.to_string_lossy().to_string()),
            modified: metadata.modified()
                .ok()
                .and_then(|time| time.duration_since(std::time::UNIX_EPOCH).ok())
                .map(|duration| duration.as_secs().to_string()),
        };
        
        Ok(file_info)
    }
}

