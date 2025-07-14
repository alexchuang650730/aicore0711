"""
Project Analyzer MCP - 項目分析器
PowerAutomation v4.6.1 核心競爭優勢組件

與Manus競爭的關鍵差異：
- 完整項目架構理解 vs 片段式理解
- 深度依賴關係分析
- 智能API端點檢測  
- 全局代碼上下文感知
- 實時項目健康監控
- 架構演進追蹤
"""

import asyncio
import logging
import ast
import json
import re
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import subprocess
import networkx as nx
from collections import defaultdict

logger = logging.getLogger(__name__)


class ProjectType(Enum):
    """項目類型"""
    WEB_APPLICATION = "web_application"
    API_SERVICE = "api_service"
    DESKTOP_APPLICATION = "desktop_application"
    LIBRARY = "library"
    CLI_TOOL = "cli_tool"
    MICROSERVICE = "microservice"
    DATA_PIPELINE = "data_pipeline"
    ML_PROJECT = "ml_project"
    UNKNOWN = "unknown"


class ArchitecturePattern(Enum):
    """架構模式"""
    MVC = "mvc"
    MVP = "mvp"
    MVVM = "mvvm"
    LAYERED = "layered"
    MICROSERVICES = "microservices"
    MONOLITHIC = "monolithic"
    EVENT_DRIVEN = "event_driven"
    PIPE_FILTER = "pipe_filter"
    CLIENT_SERVER = "client_server"
    PEER_TO_PEER = "peer_to_peer"


class ComponentType(Enum):
    """組件類型"""
    CONTROLLER = "controller"
    MODEL = "model"
    VIEW = "view"
    SERVICE = "service"
    REPOSITORY = "repository"
    UTILITY = "utility"
    CONFIG = "config"
    MIDDLEWARE = "middleware"
    API_ENDPOINT = "api_endpoint"
    DATABASE = "database"
    EXTERNAL_SERVICE = "external_service"


@dataclass
class CodeMetrics:
    """代碼指標"""
    lines_of_code: int
    cyclomatic_complexity: int
    maintainability_index: float
    technical_debt_ratio: float
    test_coverage: float
    duplication_ratio: float


@dataclass
class ProjectComponent:
    """項目組件"""
    id: str
    name: str
    type: ComponentType
    file_path: str
    dependencies: List[str]
    dependents: List[str]
    interfaces: List[str]
    metrics: CodeMetrics
    description: str
    is_core: bool = False
    
    def __post_init__(self):
        if not self.dependencies:
            self.dependencies = []
        if not self.dependents:
            self.dependents = []
        if not self.interfaces:
            self.interfaces = []


@dataclass
class APIEndpoint:
    """API端點"""
    path: str
    method: str
    handler_function: str
    file_path: str
    parameters: List[Dict[str, Any]]
    response_type: str
    middleware: List[str]
    authentication_required: bool
    documentation: str = ""
    
    def __post_init__(self):
        if not self.parameters:
            self.parameters = []
        if not self.middleware:
            self.middleware = []


@dataclass
class DependencyRelation:
    """依賴關係"""
    source: str
    target: str
    type: str  # "import", "inheritance", "composition", "aggregation"
    strength: float  # 0.0 - 1.0
    is_circular: bool = False


@dataclass
class ProjectArchitecture:
    """項目架構"""
    project_type: ProjectType
    architecture_pattern: ArchitecturePattern
    components: List[ProjectComponent]
    api_endpoints: List[APIEndpoint]
    dependencies: List[DependencyRelation]
    entry_points: List[str]
    configuration_files: List[str]
    database_schemas: List[str]
    external_services: List[str]
    metrics: CodeMetrics
    health_score: float


class CodeParsingEngine:
    """代碼解析引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def parse_python_file(self, file_path: Path) -> Dict[str, Any]:
        """解析Python文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            return {
                "classes": self._extract_classes(tree),
                "functions": self._extract_functions(tree),
                "imports": self._extract_imports(tree),
                "constants": self._extract_constants(tree),
                "decorators": self._extract_decorators(tree),
                "api_endpoints": self._extract_api_endpoints(tree, content),
                "complexity": self._calculate_complexity(tree),
                "lines_of_code": len(content.split('\n'))
            }
            
        except Exception as e:
            self.logger.error(f"解析文件失敗 {file_path}: {e}")
            return {}
    
    def _extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """提取類定義"""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "line_number": node.lineno,
                    "bases": [self._get_name(base) for base in node.bases],
                    "methods": [],
                    "decorators": [self._get_name(dec) for dec in node.decorator_list]
                }
                
                # 提取方法
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = {
                            "name": item.name,
                            "line_number": item.lineno,
                            "args": [arg.arg for arg in item.args.args],
                            "decorators": [self._get_name(dec) for dec in item.decorator_list],
                            "is_private": item.name.startswith('_'),
                            "is_static": any(self._get_name(dec) == "staticmethod" for dec in item.decorator_list),
                            "is_class_method": any(self._get_name(dec) == "classmethod" for dec in item.decorator_list)
                        }
                        class_info["methods"].append(method_info)
                
                classes.append(class_info)
        
        return classes
    
    def _extract_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """提取函數定義"""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not self._is_method(node, tree):
                function_info = {
                    "name": node.name,
                    "line_number": node.lineno,
                    "args": [arg.arg for arg in node.args.args],
                    "decorators": [self._get_name(dec) for dec in node.decorator_list],
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "return_annotation": self._get_name(node.returns) if node.returns else None,
                    "complexity": self._calculate_function_complexity(node)
                }
                functions.append(function_info)
        
        return functions
    
    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """提取導入語句"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "type": "import",
                        "module": alias.name,
                        "alias": alias.asname,
                        "line_number": node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imports.append({
                        "type": "from_import",
                        "module": node.module,
                        "name": alias.name,
                        "alias": alias.asname,
                        "line_number": node.lineno
                    })
        
        return imports
    
    def _extract_constants(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """提取常量定義"""
        constants = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        constants.append({
                            "name": target.id,
                            "line_number": node.lineno,
                            "value": self._get_literal_value(node.value)
                        })
        
        return constants
    
    def _extract_decorators(self, tree: ast.AST) -> Set[str]:
        """提取裝飾器"""
        decorators = set()
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    decorators.add(self._get_name(dec))
        
        return list(decorators)
    
    def _extract_api_endpoints(self, tree: ast.AST, content: str) -> List[Dict[str, Any]]:
        """提取API端點"""
        endpoints = []
        
        # 檢查Flask路由
        flask_routes = self._extract_flask_routes(tree)
        endpoints.extend(flask_routes)
        
        # 檢查FastAPI路由
        fastapi_routes = self._extract_fastapi_routes(tree)
        endpoints.extend(fastapi_routes)
        
        # 檢查Django URL模式
        django_urls = self._extract_django_urls(content)
        endpoints.extend(django_urls)
        
        return endpoints
    
    def _extract_flask_routes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """提取Flask路由"""
        routes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call) and self._get_name(dec.func) in ["route", "app.route"]:
                        route_info = {
                            "framework": "flask",
                            "function": node.name,
                            "line_number": node.lineno,
                            "path": self._get_literal_value(dec.args[0]) if dec.args else "",
                            "methods": []
                        }
                        
                        # 提取HTTP方法
                        for keyword in dec.keywords:
                            if keyword.arg == "methods":
                                if isinstance(keyword.value, ast.List):
                                    route_info["methods"] = [
                                        self._get_literal_value(elt) for elt in keyword.value.elts
                                    ]
                        
                        routes.append(route_info)
        
        return routes
    
    def _extract_fastapi_routes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """提取FastAPI路由"""
        routes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call):
                        func_name = self._get_name(dec.func)
                        if func_name in ["app.get", "app.post", "app.put", "app.delete", "app.patch"]:
                            method = func_name.split(".")[-1].upper()
                            route_info = {
                                "framework": "fastapi",
                                "function": node.name,
                                "line_number": node.lineno,
                                "path": self._get_literal_value(dec.args[0]) if dec.args else "",
                                "methods": [method]
                            }
                            routes.append(route_info)
        
        return routes
    
    def _extract_django_urls(self, content: str) -> List[Dict[str, Any]]:
        """提取Django URL模式"""
        routes = []
        
        # 簡化的Django URL提取
        url_patterns = re.findall(r"path\s*\(\s*['\"]([^'\"]+)['\"]", content)
        
        for i, pattern in enumerate(url_patterns):
            routes.append({
                "framework": "django",
                "path": pattern,
                "line_number": i + 1,  # 簡化處理
                "methods": ["GET", "POST"]  # Django默認支持所有方法
            })
        
        return routes
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """計算循環複雜度"""
        complexity = 1  # 基礎複雜度
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.comprehension):
                complexity += 1
        
        return complexity
    
    def _calculate_function_complexity(self, func_node: ast.FunctionDef) -> int:
        """計算函數複雜度"""
        complexity = 1
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
        
        return complexity
    
    def _get_name(self, node: ast.AST) -> str:
        """獲取AST節點名稱"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        else:
            return str(node.__class__.__name__)
    
    def _get_literal_value(self, node: ast.AST) -> Any:
        """獲取字面值"""
        if isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.List):
            return [self._get_literal_value(elt) for elt in node.elts]
        else:
            return None
    
    def _is_method(self, func_node: ast.FunctionDef, tree: ast.AST) -> bool:
        """檢查是否為類方法"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if func_node in node.body:
                    return True
        return False


class DependencyAnalyzer:
    """依賴關係分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.dependency_graph = nx.DiGraph()
    
    async def analyze_dependencies(self, project_path: Path) -> List[DependencyRelation]:
        """分析項目依賴關係"""
        dependencies = []
        
        # 收集所有Python文件
        python_files = list(project_path.glob("**/*.py"))
        
        # 解析每個文件的導入關係
        parser = CodeParsingEngine()
        file_imports = {}
        
        for file_path in python_files:
            relative_path = file_path.relative_to(project_path)
            parsed_data = await parser.parse_python_file(file_path)
            file_imports[str(relative_path)] = parsed_data.get("imports", [])
        
        # 構建依賴關係
        for file_path, imports in file_imports.items():
            for import_info in imports:
                target_module = import_info.get("module", "")
                
                # 檢查是否為內部模塊
                if self._is_internal_module(target_module, project_path):
                    dependency = DependencyRelation(
                        source=file_path,
                        target=target_module,
                        type="import",
                        strength=self._calculate_dependency_strength(import_info)
                    )
                    dependencies.append(dependency)
                    
                    # 添加到圖中
                    self.dependency_graph.add_edge(file_path, target_module)
        
        # 檢查循環依賴
        cycles = list(nx.simple_cycles(self.dependency_graph))
        for cycle in cycles:
            for i in range(len(cycle)):
                source = cycle[i]
                target = cycle[(i + 1) % len(cycle)]
                
                # 標記循環依賴
                for dep in dependencies:
                    if dep.source == source and dep.target == target:
                        dep.is_circular = True
        
        return dependencies
    
    def _is_internal_module(self, module_name: str, project_path: Path) -> bool:
        """檢查是否為內部模塊"""
        if not module_name:
            return False
        
        # 檢查是否為相對導入
        if module_name.startswith('.'):
            return True
        
        # 檢查模塊文件是否存在於項目中
        module_parts = module_name.split('.')
        potential_path = project_path
        
        for part in module_parts:
            potential_path = potential_path / part
            if (potential_path.with_suffix('.py')).exists() or (potential_path / '__init__.py').exists():
                return True
        
        return False
    
    def _calculate_dependency_strength(self, import_info: Dict[str, Any]) -> float:
        """計算依賴強度"""
        # 簡化的依賴強度計算
        if import_info.get("type") == "from_import":
            return 0.8  # from import 通常表示更強的依賴
        else:
            return 0.5  # import 表示較弱的依賴
    
    def get_dependency_metrics(self) -> Dict[str, Any]:
        """獲取依賴指標"""
        if not self.dependency_graph.nodes():
            return {}
        
        return {
            "total_nodes": self.dependency_graph.number_of_nodes(),
            "total_edges": self.dependency_graph.number_of_edges(),
            "density": nx.density(self.dependency_graph),
            "cycles": len(list(nx.simple_cycles(self.dependency_graph))),
            "strongly_connected_components": len(list(nx.strongly_connected_components(self.dependency_graph))),
            "average_degree": sum(dict(self.dependency_graph.degree()).values()) / self.dependency_graph.number_of_nodes()
        }


class ArchitectureDetector:
    """架構模式檢測器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def detect_architecture_pattern(self, project_path: Path, components: List[ProjectComponent]) -> ArchitecturePattern:
        """檢測架構模式"""
        
        # 分析目錄結構
        dir_structure = self._analyze_directory_structure(project_path)
        
        # 分析組件類型分布
        component_types = [comp.type for comp in components]
        
        # 檢查MVC模式
        if self._is_mvc_pattern(dir_structure, component_types):
            return ArchitecturePattern.MVC
        
        # 檢查分層架構
        if self._is_layered_pattern(dir_structure):
            return ArchitecturePattern.LAYERED
        
        # 檢查微服務架構
        if self._is_microservices_pattern(project_path, dir_structure):
            return ArchitecturePattern.MICROSERVICES
        
        # 檢查事件驅動架構
        if self._is_event_driven_pattern(components):
            return ArchitecturePattern.EVENT_DRIVEN
        
        return ArchitecturePattern.MONOLITHIC
    
    def _analyze_directory_structure(self, project_path: Path) -> Dict[str, List[str]]:
        """分析目錄結構"""
        structure = defaultdict(list)
        
        for item in project_path.rglob("*"):
            if item.is_dir():
                parent = item.parent.name if item.parent != project_path else "root"
                structure[parent].append(item.name)
        
        return dict(structure)
    
    def _is_mvc_pattern(self, dir_structure: Dict[str, List[str]], component_types: List[ComponentType]) -> bool:
        """檢查是否為MVC模式"""
        mvc_indicators = ["models", "views", "controllers", "templates"]
        
        # 檢查目錄結構
        all_dirs = set()
        for dirs in dir_structure.values():
            all_dirs.update([d.lower() for d in dirs])
        
        mvc_score = sum(1 for indicator in mvc_indicators if indicator in all_dirs)
        
        # 檢查組件類型
        has_models = ComponentType.MODEL in component_types
        has_views = ComponentType.VIEW in component_types
        has_controllers = ComponentType.CONTROLLER in component_types
        
        return mvc_score >= 2 and (has_models or has_views or has_controllers)
    
    def _is_layered_pattern(self, dir_structure: Dict[str, List[str]]) -> bool:
        """檢查是否為分層架構"""
        layer_indicators = ["presentation", "business", "data", "service", "repository", "dao"]
        
        all_dirs = set()
        for dirs in dir_structure.values():
            all_dirs.update([d.lower() for d in dirs])
        
        layer_score = sum(1 for indicator in layer_indicators if indicator in all_dirs)
        
        return layer_score >= 2
    
    def _is_microservices_pattern(self, project_path: Path, dir_structure: Dict[str, List[str]]) -> bool:
        """檢查是否為微服務架構"""
        # 檢查是否有Docker配置
        has_docker = (project_path / "Dockerfile").exists() or (project_path / "docker-compose.yml").exists()
        
        # 檢查是否有多個服務目錄
        service_indicators = ["services", "microservices", "apps"]
        
        all_dirs = set()
        for dirs in dir_structure.values():
            all_dirs.update([d.lower() for d in dirs])
        
        has_service_structure = any(indicator in all_dirs for indicator in service_indicators)
        
        return has_docker and has_service_structure
    
    def _is_event_driven_pattern(self, components: List[ProjectComponent]) -> bool:
        """檢查是否為事件驅動架構"""
        event_indicators = ["event", "message", "queue", "broker", "publisher", "subscriber"]
        
        component_names = [comp.name.lower() for comp in components]
        
        event_score = sum(1 for name in component_names 
                         if any(indicator in name for indicator in event_indicators))
        
        return event_score >= 2


class ProjectAnalyzerMCP:
    """項目分析器MCP主管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.code_parser = CodeParsingEngine()
        self.dependency_analyzer = DependencyAnalyzer()
        self.architecture_detector = ArchitectureDetector()
        self.analysis_cache = {}
    
    async def initialize(self):
        """初始化項目分析器MCP"""
        self.logger.info("🏗️ 初始化Project Analyzer MCP - PowerAutomation項目理解核心")
        
        # 初始化分析引擎
        await self._initialize_analysis_engines()
        
        self.logger.info("✅ Project Analyzer MCP初始化完成")
    
    async def analyze_project(self, project_path: str) -> ProjectArchitecture:
        """完整項目分析"""
        self.logger.info(f"🔍 開始分析項目: {project_path}")
        
        project_path = Path(project_path)
        
        # 檢查緩存
        cache_key = f"{project_path}_{os.path.getmtime(project_path)}"
        if cache_key in self.analysis_cache:
            self.logger.info("使用緩存的分析結果")
            return self.analysis_cache[cache_key]
        
        # 檢測項目類型
        project_type = await self._detect_project_type(project_path)
        
        # 分析組件
        components = await self._analyze_components(project_path)
        
        # 分析API端點
        api_endpoints = await self._analyze_api_endpoints(project_path)
        
        # 分析依賴關係
        dependencies = await self.dependency_analyzer.analyze_dependencies(project_path)
        
        # 檢測架構模式
        architecture_pattern = await self.architecture_detector.detect_architecture_pattern(project_path, components)
        
        # 找出入口點
        entry_points = await self._find_entry_points(project_path)
        
        # 找出配置文件
        config_files = await self._find_configuration_files(project_path)
        
        # 分析數據庫模式
        db_schemas = await self._analyze_database_schemas(project_path)
        
        # 識別外部服務
        external_services = await self._identify_external_services(project_path)
        
        # 計算項目指標
        project_metrics = await self._calculate_project_metrics(project_path, components)
        
        # 計算健康分數
        health_score = self._calculate_project_health_score(components, dependencies, project_metrics)
        
        # 創建項目架構對象
        architecture = ProjectArchitecture(
            project_type=project_type,
            architecture_pattern=architecture_pattern,
            components=components,
            api_endpoints=api_endpoints,
            dependencies=dependencies,
            entry_points=entry_points,
            configuration_files=config_files,
            database_schemas=db_schemas,
            external_services=external_services,
            metrics=project_metrics,
            health_score=health_score
        )
        
        # 緩存結果
        self.analysis_cache[cache_key] = architecture
        
        # 保存分析報告
        await self._save_analysis_report(architecture, project_path)
        
        self.logger.info(f"✅ 項目分析完成: {len(components)} 個組件，{len(api_endpoints)} 個API端點")
        
        return architecture
    
    async def _detect_project_type(self, project_path: Path) -> ProjectType:
        """檢測項目類型"""
        
        # 檢查特徵文件
        if (project_path / "manage.py").exists():
            return ProjectType.WEB_APPLICATION  # Django
        
        if (project_path / "app.py").exists() or (project_path / "main.py").exists():
            return ProjectType.WEB_APPLICATION  # Flask/FastAPI
        
        if (project_path / "setup.py").exists() or (project_path / "pyproject.toml").exists():
            return ProjectType.LIBRARY
        
        if (project_path / "__main__.py").exists():
            return ProjectType.CLI_TOOL
        
        # 檢查目錄結構
        if any((project_path / name).exists() for name in ["api", "endpoints", "routes"]):
            return ProjectType.API_SERVICE
        
        if (project_path / "requirements.txt").exists():
            with open(project_path / "requirements.txt", 'r') as f:
                content = f.read()
                if any(keyword in content for keyword in ["flask", "django", "fastapi"]):
                    return ProjectType.WEB_APPLICATION
                elif any(keyword in content for keyword in ["sklearn", "tensorflow", "pytorch"]):
                    return ProjectType.ML_PROJECT
        
        return ProjectType.UNKNOWN
    
    async def _analyze_components(self, project_path: Path) -> List[ProjectComponent]:
        """分析項目組件"""
        components = []
        
        # 遍歷所有Python文件
        for py_file in project_path.glob("**/*.py"):
            if py_file.name.startswith('.') or '__pycache__' in str(py_file):
                continue
            
            parsed_data = await self.code_parser.parse_python_file(py_file)
            
            if not parsed_data:
                continue
            
            # 確定組件類型
            component_type = self._determine_component_type(py_file, parsed_data)
            
            # 計算組件指標
            metrics = self._calculate_component_metrics(parsed_data)
            
            # 提取依賴關係
            dependencies = self._extract_component_dependencies(parsed_data)
            
            # 提取接口
            interfaces = self._extract_component_interfaces(parsed_data)
            
            component = ProjectComponent(
                id=str(py_file.relative_to(project_path)),
                name=py_file.stem,
                type=component_type,
                file_path=str(py_file),
                dependencies=dependencies,
                dependents=[],  # 將在後續分析中填充
                interfaces=interfaces,
                metrics=metrics,
                description=self._generate_component_description(parsed_data),
                is_core=self._is_core_component(py_file, parsed_data)
            )
            
            components.append(component)
        
        # 填充依賴者信息
        self._populate_dependents(components)
        
        return components
    
    def _determine_component_type(self, file_path: Path, parsed_data: Dict[str, Any]) -> ComponentType:
        """確定組件類型"""
        file_name = file_path.name.lower()
        
        # 基於文件名
        if "controller" in file_name:
            return ComponentType.CONTROLLER
        elif "model" in file_name:
            return ComponentType.MODEL
        elif "view" in file_name:
            return ComponentType.VIEW
        elif "service" in file_name:
            return ComponentType.SERVICE
        elif "repository" in file_name or "dao" in file_name:
            return ComponentType.REPOSITORY
        elif "config" in file_name or "setting" in file_name:
            return ComponentType.CONFIG
        elif "middleware" in file_name:
            return ComponentType.MIDDLEWARE
        elif "util" in file_name or "helper" in file_name:
            return ComponentType.UTILITY
        
        # 基於API端點
        if parsed_data.get("api_endpoints"):
            return ComponentType.API_ENDPOINT
        
        # 基於類和函數特徵
        classes = parsed_data.get("classes", [])
        functions = parsed_data.get("functions", [])
        
        if classes:
            # 檢查類名模式
            for cls in classes:
                class_name = cls["name"].lower()
                if "model" in class_name:
                    return ComponentType.MODEL
                elif "controller" in class_name:
                    return ComponentType.CONTROLLER
                elif "service" in class_name:
                    return ComponentType.SERVICE
                elif "repository" in class_name:
                    return ComponentType.REPOSITORY
        
        return ComponentType.UTILITY
    
    def _calculate_component_metrics(self, parsed_data: Dict[str, Any]) -> CodeMetrics:
        """計算組件指標"""
        lines_of_code = parsed_data.get("lines_of_code", 0)
        complexity = parsed_data.get("complexity", 1)
        
        # 簡化的指標計算
        maintainability_index = max(0, 171 - 5.2 * complexity - 0.23 * lines_of_code)
        technical_debt_ratio = min(100, complexity / lines_of_code * 100) if lines_of_code > 0 else 0
        
        return CodeMetrics(
            lines_of_code=lines_of_code,
            cyclomatic_complexity=complexity,
            maintainability_index=maintainability_index,
            technical_debt_ratio=technical_debt_ratio,
            test_coverage=0.0,  # 需要額外分析
            duplication_ratio=0.0  # 需要額外分析
        )
    
    def _extract_component_dependencies(self, parsed_data: Dict[str, Any]) -> List[str]:
        """提取組件依賴"""
        dependencies = []
        
        imports = parsed_data.get("imports", [])
        for import_info in imports:
            if import_info.get("module"):
                dependencies.append(import_info["module"])
        
        return dependencies
    
    def _extract_component_interfaces(self, parsed_data: Dict[str, Any]) -> List[str]:
        """提取組件接口"""
        interfaces = []
        
        # 提取公共方法作為接口
        classes = parsed_data.get("classes", [])
        for cls in classes:
            for method in cls.get("methods", []):
                if not method["is_private"]:
                    interfaces.append(f"{cls['name']}.{method['name']}")
        
        # 提取公共函數作為接口
        functions = parsed_data.get("functions", [])
        for func in functions:
            if not func["name"].startswith("_"):
                interfaces.append(func["name"])
        
        return interfaces
    
    def _generate_component_description(self, parsed_data: Dict[str, Any]) -> str:
        """生成組件描述"""
        classes = parsed_data.get("classes", [])
        functions = parsed_data.get("functions", [])
        api_endpoints = parsed_data.get("api_endpoints", [])
        
        parts = []
        
        if classes:
            parts.append(f"{len(classes)} 個類")
        
        if functions:
            parts.append(f"{len(functions)} 個函數")
        
        if api_endpoints:
            parts.append(f"{len(api_endpoints)} 個API端點")
        
        return "包含 " + "、".join(parts) if parts else "代碼組件"
    
    def _is_core_component(self, file_path: Path, parsed_data: Dict[str, Any]) -> bool:
        """判斷是否為核心組件"""
        # 基於文件名
        core_names = ["main", "app", "core", "engine", "manager"]
        if any(name in file_path.name.lower() for name in core_names):
            return True
        
        # 基於API端點數量
        api_endpoints = parsed_data.get("api_endpoints", [])
        if len(api_endpoints) > 5:
            return True
        
        # 基於代碼複雜度
        complexity = parsed_data.get("complexity", 0)
        if complexity > 20:
            return True
        
        return False
    
    def _populate_dependents(self, components: List[ProjectComponent]):
        """填充依賴者信息"""
        # 構建依賴關係映射
        dependency_map = {}
        
        for component in components:
            for dep in component.dependencies:
                if dep not in dependency_map:
                    dependency_map[dep] = []
                dependency_map[dep].append(component.id)
        
        # 更新依賴者信息
        for component in components:
            component.dependents = dependency_map.get(component.id, [])
    
    async def _analyze_api_endpoints(self, project_path: Path) -> List[APIEndpoint]:
        """分析API端點"""
        endpoints = []
        
        for py_file in project_path.glob("**/*.py"):
            parsed_data = await self.code_parser.parse_python_file(py_file)
            
            file_endpoints = parsed_data.get("api_endpoints", [])
            
            for endpoint_data in file_endpoints:
                endpoint = APIEndpoint(
                    path=endpoint_data.get("path", ""),
                    method=endpoint_data.get("methods", ["GET"])[0] if endpoint_data.get("methods") else "GET",
                    handler_function=endpoint_data.get("function", ""),
                    file_path=str(py_file),
                    parameters=[],  # 需要進一步分析
                    response_type="",  # 需要進一步分析
                    middleware=[],  # 需要進一步分析
                    authentication_required=False,  # 需要進一步分析
                    documentation=""
                )
                endpoints.append(endpoint)
        
        return endpoints
    
    async def _find_entry_points(self, project_path: Path) -> List[str]:
        """找出入口點"""
        entry_points = []
        
        # 常見的入口點文件
        entry_files = ["main.py", "app.py", "run.py", "manage.py", "__main__.py"]
        
        for entry_file in entry_files:
            if (project_path / entry_file).exists():
                entry_points.append(entry_file)
        
        return entry_points
    
    async def _find_configuration_files(self, project_path: Path) -> List[str]:
        """找出配置文件"""
        config_files = []
        
        # 常見的配置文件模式
        config_patterns = [
            "*.ini", "*.conf", "*.config", "*.yaml", "*.yml", "*.json",
            "settings.py", "config.py", ".env", "requirements.txt"
        ]
        
        for pattern in config_patterns:
            for config_file in project_path.glob(f"**/{pattern}"):
                config_files.append(str(config_file.relative_to(project_path)))
        
        return config_files
    
    async def _analyze_database_schemas(self, project_path: Path) -> List[str]:
        """分析數據庫模式"""
        schemas = []
        
        # 查找數據庫相關文件
        db_patterns = ["*.sql", "migrations/*.py", "models/*.py"]
        
        for pattern in db_patterns:
            for db_file in project_path.glob(f"**/{pattern}"):
                schemas.append(str(db_file.relative_to(project_path)))
        
        return schemas
    
    async def _identify_external_services(self, project_path: Path) -> List[str]:
        """識別外部服務"""
        external_services = set()
        
        # 檢查requirements.txt
        requirements_file = project_path / "requirements.txt"
        if requirements_file.exists():
            with open(requirements_file, 'r') as f:
                content = f.read()
                
                # 常見的外部服務庫
                service_libraries = {
                    "requests": "HTTP API",
                    "boto3": "AWS Services",
                    "redis": "Redis",
                    "psycopg2": "PostgreSQL",
                    "pymongo": "MongoDB",
                    "elasticsearch": "Elasticsearch",
                    "celery": "Task Queue",
                    "kafka": "Apache Kafka"
                }
                
                for lib, service in service_libraries.items():
                    if lib in content:
                        external_services.add(service)
        
        return list(external_services)
    
    async def _calculate_project_metrics(self, project_path: Path, components: List[ProjectComponent]) -> CodeMetrics:
        """計算項目整體指標"""
        total_loc = sum(comp.metrics.lines_of_code for comp in components)
        avg_complexity = sum(comp.metrics.cyclomatic_complexity for comp in components) / len(components) if components else 0
        avg_maintainability = sum(comp.metrics.maintainability_index for comp in components) / len(components) if components else 0
        avg_tech_debt = sum(comp.metrics.technical_debt_ratio for comp in components) / len(components) if components else 0
        
        return CodeMetrics(
            lines_of_code=total_loc,
            cyclomatic_complexity=int(avg_complexity),
            maintainability_index=avg_maintainability,
            technical_debt_ratio=avg_tech_debt,
            test_coverage=0.0,  # 需要額外計算
            duplication_ratio=0.0  # 需要額外計算
        )
    
    def _calculate_project_health_score(self, components: List[ProjectComponent], 
                                      dependencies: List[DependencyRelation], 
                                      metrics: CodeMetrics) -> float:
        """計算項目健康分數"""
        score = 100.0
        
        # 基於複雜度扣分
        if metrics.cyclomatic_complexity > 20:
            score -= 20
        elif metrics.cyclomatic_complexity > 10:
            score -= 10
        
        # 基於可維護性指數
        if metrics.maintainability_index < 60:
            score -= 15
        elif metrics.maintainability_index < 80:
            score -= 10
        
        # 基於技術債務
        if metrics.technical_debt_ratio > 30:
            score -= 15
        elif metrics.technical_debt_ratio > 20:
            score -= 10
        
        # 基於循環依賴
        circular_deps = [dep for dep in dependencies if dep.is_circular]
        if circular_deps:
            score -= len(circular_deps) * 5
        
        # 基於組件數量和結構
        if len(components) > 100:
            score -= 5  # 過於複雜
        elif len(components) < 5:
            score -= 5  # 過於簡單
        
        return max(0.0, min(100.0, score))
    
    async def _save_analysis_report(self, architecture: ProjectArchitecture, project_path: Path):
        """保存分析報告"""
        reports_dir = Path("project_analysis_reports")
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = reports_dir / f"project_analysis_{project_path.name}_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(architecture), f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"項目分析報告已保存: {report_file}")
    
    async def _initialize_analysis_engines(self):
        """初始化分析引擎"""
        # 初始化各個分析組件
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """獲取組件狀態"""
        return {
            "component": "Project Analyzer MCP",
            "version": "4.6.1", 
            "status": "running",
            "cached_analyses": len(self.analysis_cache),
            "capabilities": [
                "project_type_detection",
                "architecture_pattern_recognition",
                "component_analysis",
                "dependency_mapping", 
                "api_endpoint_discovery",
                "code_metrics_calculation",
                "health_score_assessment"
            ],
            "competitive_advantages": [
                "complete_project_understanding",
                "deep_dependency_analysis",
                "intelligent_architecture_detection",
                "real_time_health_monitoring",
                "vs_manus_fragment_understanding"
            ]
        }


# 單例實例
project_analyzer_mcp = ProjectAnalyzerMCP()