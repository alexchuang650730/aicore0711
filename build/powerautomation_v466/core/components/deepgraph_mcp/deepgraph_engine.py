#!/usr/bin/env python3
"""
DeepGraph MCP - 深度圖形分析框架
集成到PowerAutomation v4.6.2的核心圖分析引擎
"""

import asyncio
import logging
import json
import networkx as nx
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import ast
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class GraphType(Enum):
    """圖類型枚舉"""
    CODE_DEPENDENCY = "code_dependency"
    WORKFLOW = "workflow"
    UI_COMPONENT = "ui_component"
    TEST_DEPENDENCY = "test_dependency"
    DATA_FLOW = "data_flow"
    EXECUTION_PATH = "execution_path"

class NodeType(Enum):
    """節點類型枚舉"""
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    COMPONENT = "component"
    WORKFLOW_STEP = "workflow_step"
    TEST_CASE = "test_case"
    UI_ELEMENT = "ui_element"

@dataclass
class GraphNode:
    """圖節點數據結構"""
    id: str
    type: NodeType
    name: str
    properties: Dict[str, Any]
    metadata: Dict[str, Any]
    coordinates: Optional[Tuple[float, float]] = None

@dataclass
class GraphEdge:
    """圖邊數據結構"""
    source: str
    target: str
    relationship: str
    weight: float = 1.0
    properties: Dict[str, Any] = None

@dataclass
class GraphAnalysisResult:
    """圖分析結果"""
    graph_id: str
    graph_type: GraphType
    nodes_count: int
    edges_count: int
    metrics: Dict[str, float]
    insights: List[str]
    recommendations: List[str]
    optimization_opportunities: List[Dict[str, Any]]

class DeepGraphEngine:
    """深度圖分析引擎"""
    
    def __init__(self):
        self.graphs: Dict[str, nx.DiGraph] = {}
        self.analysis_cache: Dict[str, GraphAnalysisResult] = {}
        self.node_embeddings: Dict[str, np.ndarray] = {}
        
    async def create_graph(self, graph_id: str, graph_type: GraphType) -> nx.DiGraph:
        """創建新圖"""
        graph = nx.DiGraph()
        graph.graph['type'] = graph_type
        graph.graph['created_at'] = asyncio.get_event_loop().time()
        self.graphs[graph_id] = graph
        
        logger.info(f"創建圖: {graph_id}, 類型: {graph_type.value}")
        return graph
    
    async def add_node(self, graph_id: str, node: GraphNode) -> None:
        """添加節點到圖"""
        if graph_id not in self.graphs:
            raise ValueError(f"圖 {graph_id} 不存在")
        
        graph = self.graphs[graph_id]
        graph.add_node(
            node.id,
            type=node.type.value,
            name=node.name,
            properties=node.properties,
            metadata=node.metadata,
            coordinates=node.coordinates
        )
        
        # 生成節點嵌入
        embedding = await self._generate_node_embedding(node)
        self.node_embeddings[f"{graph_id}:{node.id}"] = embedding
    
    async def add_edge(self, graph_id: str, edge: GraphEdge) -> None:
        """添加邊到圖"""
        if graph_id not in self.graphs:
            raise ValueError(f"圖 {graph_id} 不存在")
        
        graph = self.graphs[graph_id]
        graph.add_edge(
            edge.source,
            edge.target,
            relationship=edge.relationship,
            weight=edge.weight,
            properties=edge.properties or {}
        )
    
    async def analyze_graph(self, graph_id: str) -> GraphAnalysisResult:
        """深度分析圖結構"""
        if graph_id not in self.graphs:
            raise ValueError(f"圖 {graph_id} 不存在")
        
        graph = self.graphs[graph_id]
        graph_type = GraphType(graph.graph['type'])
        
        # 基礎度量
        metrics = await self._calculate_graph_metrics(graph)
        
        # 深度分析
        insights = await self._generate_insights(graph, metrics)
        
        # 優化建議
        recommendations = await self._generate_recommendations(graph, metrics)
        
        # 優化機會
        optimization_opportunities = await self._find_optimization_opportunities(graph)
        
        result = GraphAnalysisResult(
            graph_id=graph_id,
            graph_type=graph_type,
            nodes_count=graph.number_of_nodes(),
            edges_count=graph.number_of_edges(),
            metrics=metrics,
            insights=insights,
            recommendations=recommendations,
            optimization_opportunities=optimization_opportunities
        )
        
        self.analysis_cache[graph_id] = result
        return result
    
    async def _calculate_graph_metrics(self, graph: nx.DiGraph) -> Dict[str, float]:
        """計算圖度量指標"""
        metrics = {}
        
        try:
            # 基礎度量
            metrics['density'] = nx.density(graph)
            metrics['average_clustering'] = nx.average_clustering(graph.to_undirected())
            
            # 中心性度量
            betweenness = nx.betweenness_centrality(graph)
            closeness = nx.closeness_centrality(graph)
            pagerank = nx.pagerank(graph)
            
            metrics['max_betweenness'] = max(betweenness.values()) if betweenness else 0
            metrics['avg_betweenness'] = np.mean(list(betweenness.values())) if betweenness else 0
            metrics['max_closeness'] = max(closeness.values()) if closeness else 0
            metrics['avg_closeness'] = np.mean(list(closeness.values())) if closeness else 0
            metrics['max_pagerank'] = max(pagerank.values()) if pagerank else 0
            
            # 連通性度量
            if graph.number_of_nodes() > 0:
                metrics['is_connected'] = float(nx.is_weakly_connected(graph))
                components = list(nx.weakly_connected_components(graph))
                metrics['connected_components'] = len(components)
                metrics['largest_component_size'] = len(max(components, key=len)) if components else 0
            
            # 路徑度量
            if nx.is_weakly_connected(graph):
                try:
                    metrics['average_shortest_path'] = nx.average_shortest_path_length(graph.to_undirected())
                    metrics['diameter'] = nx.diameter(graph.to_undirected())
                except:
                    metrics['average_shortest_path'] = 0
                    metrics['diameter'] = 0
            
            # 度分佈
            degrees = [d for n, d in graph.degree()]
            if degrees:
                metrics['max_degree'] = max(degrees)
                metrics['avg_degree'] = np.mean(degrees)
                metrics['degree_variance'] = np.var(degrees)
            
        except Exception as e:
            logger.warning(f"計算圖度量時出錯: {e}")
            
        return metrics
    
    async def _generate_insights(self, graph: nx.DiGraph, metrics: Dict[str, float]) -> List[str]:
        """生成圖洞察"""
        insights = []
        
        # 複雜度分析
        if metrics.get('density', 0) > 0.3:
            insights.append("圖結構密度較高，存在較多交互關係，可能需要模塊化重構")
        
        # 中心節點分析
        if metrics.get('max_betweenness', 0) > 0.5:
            insights.append("存在關鍵中心節點，這些節點故障會嚴重影響整體功能")
        
        # 連通性分析
        if metrics.get('connected_components', 0) > 1:
            insights.append(f"圖包含 {int(metrics['connected_components'])} 個獨立組件，可能存在孤立模塊")
        
        # 度中心性分析
        if metrics.get('degree_variance', 0) > metrics.get('avg_degree', 0) * 2:
            insights.append("節點度分佈不均，存在明顯的核心節點和邊緣節點")
        
        return insights
    
    async def _generate_recommendations(self, graph: nx.DiGraph, metrics: Dict[str, float]) -> List[str]:
        """生成優化建議"""
        recommendations = []
        
        # 重構建議
        if metrics.get('density', 0) > 0.4:
            recommendations.append("建議進行模塊化重構，減少模塊間耦合")
        
        # 性能優化建議
        if metrics.get('max_degree', 0) > 20:
            recommendations.append("建議對高度節點進行負載分散，避免單點瓶頸")
        
        # 測試建議
        betweenness = nx.betweenness_centrality(graph)
        critical_nodes = [node for node, centrality in betweenness.items() if centrality > 0.3]
        if critical_nodes:
            recommendations.append(f"建議加強對關鍵節點 {critical_nodes[:3]} 的測試覆蓋")
        
        # 架構建議
        if metrics.get('connected_components', 0) > 5:
            recommendations.append("建議檢查模塊間的依賴關係，可能存在過度分散的問題")
        
        return recommendations
    
    async def _find_optimization_opportunities(self, graph: nx.DiGraph) -> List[Dict[str, Any]]:
        """發現優化機會"""
        opportunities = []
        
        # 找出可以合併的節點
        nodes_to_merge = await self._find_mergeable_nodes(graph)
        if nodes_to_merge:
            opportunities.append({
                "type": "merge_nodes",
                "description": "發現可以合併的相似節點",
                "nodes": nodes_to_merge,
                "impact": "減少複雜度，提高維護性"
            })
        
        # 找出可以分解的大節點
        large_nodes = await self._find_oversized_nodes(graph)
        if large_nodes:
            opportunities.append({
                "type": "decompose_nodes",
                "description": "發現需要分解的大型節點",
                "nodes": large_nodes,
                "impact": "提高模塊性，降低耦合"
            })
        
        # 找出缺失的連接
        missing_connections = await self._find_missing_connections(graph)
        if missing_connections:
            opportunities.append({
                "type": "add_connections",
                "description": "發現可能缺失的邏輯連接",
                "connections": missing_connections,
                "impact": "完善依賴關係，提高系統完整性"
            })
        
        return opportunities
    
    async def _find_mergeable_nodes(self, graph: nx.DiGraph) -> List[List[str]]:
        """找出可以合併的節點"""
        # 基於結構相似性找出可合併節點
        similar_groups = []
        nodes = list(graph.nodes())
        
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                similarity = await self._calculate_node_similarity(graph, node1, node2)
                if similarity > 0.8:  # 高相似度閾值
                    # 檢查是否已在某個組中
                    added = False
                    for group in similar_groups:
                        if node1 in group or node2 in group:
                            if node1 not in group:
                                group.append(node1)
                            if node2 not in group:
                                group.append(node2)
                            added = True
                            break
                    
                    if not added:
                        similar_groups.append([node1, node2])
        
        return [group for group in similar_groups if len(group) > 1]
    
    async def _find_oversized_nodes(self, graph: nx.DiGraph) -> List[str]:
        """找出過大的節點"""
        large_nodes = []
        
        for node in graph.nodes():
            degree = graph.degree(node)
            properties = graph.nodes[node].get('properties', {})
            
            # 基於度數和屬性判斷節點大小
            if degree > 15:  # 連接過多
                large_nodes.append(node)
            elif properties.get('complexity', 0) > 10:  # 複雜度過高
                large_nodes.append(node)
        
        return large_nodes
    
    async def _find_missing_connections(self, graph: nx.DiGraph) -> List[Tuple[str, str]]:
        """找出可能缺失的連接"""
        missing = []
        
        # 基於傳遞性發現缺失連接
        for node1 in graph.nodes():
            for node2 in graph.nodes():
                if node1 != node2 and not graph.has_edge(node1, node2):
                    # 檢查是否存在間接路徑
                    try:
                        path = nx.shortest_path(graph, node1, node2)
                        if len(path) == 3:  # 存在中間節點的短路徑
                            missing.append((node1, node2))
                    except nx.NetworkXNoPath:
                        continue
        
        return missing[:10]  # 限制返回數量
    
    async def _calculate_node_similarity(self, graph: nx.DiGraph, node1: str, node2: str) -> float:
        """計算節點相似度"""
        # 基於鄰居節點相似度
        neighbors1 = set(graph.neighbors(node1))
        neighbors2 = set(graph.neighbors(node2))
        
        if not neighbors1 and not neighbors2:
            return 0.0
        
        intersection = neighbors1.intersection(neighbors2)
        union = neighbors1.union(neighbors2)
        
        jaccard_similarity = len(intersection) / len(union) if union else 0
        
        # 基於節點屬性相似度
        props1 = graph.nodes[node1].get('properties', {})
        props2 = graph.nodes[node2].get('properties', {})
        
        attr_similarity = 0.0
        if props1.get('type') == props2.get('type'):
            attr_similarity += 0.3
        
        return (jaccard_similarity * 0.7 + attr_similarity * 0.3)
    
    async def _generate_node_embedding(self, node: GraphNode) -> np.ndarray:
        """生成節點嵌入向量"""
        # 簡化的節點嵌入生成
        embedding_dim = 64
        
        # 基於節點類型和屬性生成嵌入
        type_vector = np.random.normal(0, 1, embedding_dim // 2)
        prop_vector = np.random.normal(0, 1, embedding_dim // 2)
        
        # 根據節點類型調整向量
        type_multiplier = {
            NodeType.FUNCTION: 1.0,
            NodeType.CLASS: 1.2,
            NodeType.MODULE: 1.5,
            NodeType.COMPONENT: 1.1,
            NodeType.WORKFLOW_STEP: 0.9,
            NodeType.TEST_CASE: 0.8,
            NodeType.UI_ELEMENT: 1.3
        }.get(node.type, 1.0)
        
        type_vector *= type_multiplier
        
        embedding = np.concatenate([type_vector, prop_vector])
        return embedding / np.linalg.norm(embedding)  # 正規化

class CodeGraphBuilder:
    """代碼圖構建器"""
    
    def __init__(self, deep_graph_engine: DeepGraphEngine):
        self.engine = deep_graph_engine
    
    async def build_from_directory(self, directory_path: str, graph_id: str) -> GraphAnalysisResult:
        """從目錄構建代碼依賴圖"""
        print(f"🔍 開始分析代碼目錄: {directory_path}")
        
        # 創建圖
        await self.engine.create_graph(graph_id, GraphType.CODE_DEPENDENCY)
        
        # 分析Python文件
        python_files = list(Path(directory_path).rglob("*.py"))
        print(f"📁 發現 {len(python_files)} 個Python文件")
        
        # 構建節點
        for file_path in python_files:
            await self._analyze_python_file(graph_id, file_path)
        
        # 構建依賴邊
        await self._build_dependencies(graph_id, python_files)
        
        # 分析圖
        result = await self.engine.analyze_graph(graph_id)
        print(f"✅ 代碼圖分析完成: {result.nodes_count} 節點, {result.edges_count} 邊")
        
        return result
    
    async def _analyze_python_file(self, graph_id: str, file_path: Path) -> None:
        """分析Python文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # 分析模塊
            module_node = GraphNode(
                id=str(file_path),
                type=NodeType.MODULE,
                name=file_path.name,
                properties={
                    'path': str(file_path),
                    'lines': len(content.split('\n')),
                    'size': len(content)
                },
                metadata={'file_type': 'python'}
            )
            await self.engine.add_node(graph_id, module_node)
            
            # 分析類和函數
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_node = GraphNode(
                        id=f"{file_path}:{node.name}",
                        type=NodeType.FUNCTION,
                        name=node.name,
                        properties={
                            'lineno': node.lineno,
                            'args_count': len(node.args.args),
                            'is_async': isinstance(node, ast.AsyncFunctionDef)
                        },
                        metadata={'parent_module': str(file_path)}
                    )
                    await self.engine.add_node(graph_id, func_node)
                    
                    # 添加模塊到函數的邊
                    edge = GraphEdge(
                        source=str(file_path),
                        target=f"{file_path}:{node.name}",
                        relationship="contains"
                    )
                    await self.engine.add_edge(graph_id, edge)
                
                elif isinstance(node, ast.ClassDef):
                    class_node = GraphNode(
                        id=f"{file_path}:{node.name}",
                        type=NodeType.CLASS,
                        name=node.name,
                        properties={
                            'lineno': node.lineno,
                            'methods_count': len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                        },
                        metadata={'parent_module': str(file_path)}
                    )
                    await self.engine.add_node(graph_id, class_node)
                    
                    # 添加模塊到類的邊
                    edge = GraphEdge(
                        source=str(file_path),
                        target=f"{file_path}:{node.name}",
                        relationship="contains"
                    )
                    await self.engine.add_edge(graph_id, edge)
        
        except Exception as e:
            logger.warning(f"分析文件 {file_path} 時出錯: {e}")
    
    async def _build_dependencies(self, graph_id: str, python_files: List[Path]) -> None:
        """構建依賴關係"""
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # 分析import語句
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            await self._add_import_edge(graph_id, str(file_path), alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            await self._add_import_edge(graph_id, str(file_path), node.module)
            
            except Exception as e:
                logger.warning(f"分析依賴 {file_path} 時出錯: {e}")
    
    async def _add_import_edge(self, graph_id: str, source_file: str, imported_module: str) -> None:
        """添加import依賴邊"""
        # 簡化的依賴邊添加邏輯
        if imported_module.startswith('.'):  # 相對導入
            return
        
        # 檢查是否是項目內模塊
        graph = self.engine.graphs[graph_id]
        for node_id in graph.nodes():
            if imported_module in node_id:
                edge = GraphEdge(
                    source=source_file,
                    target=node_id,
                    relationship="imports"
                )
                await self.engine.add_edge(graph_id, edge)
                break

class WorkflowGraphBuilder:
    """工作流圖構建器"""
    
    def __init__(self, deep_graph_engine: DeepGraphEngine):
        self.engine = deep_graph_engine
    
    async def build_codeflow_graph(self, graph_id: str, workflow_config: Dict[str, Any]) -> GraphAnalysisResult:
        """構建CodeFlow工作流圖"""
        print("🔄 開始構建CodeFlow工作流圖")
        
        # 創建圖
        await self.engine.create_graph(graph_id, GraphType.WORKFLOW)
        
        # 添加六大工作流節點
        workflows = [
            "Code Generation",
            "UI Design", 
            "API Development",
            "Database Design",
            "Testing Automation",
            "Deployment Pipeline"
        ]
        
        for i, workflow in enumerate(workflows):
            node = GraphNode(
                id=f"workflow_{i}",
                type=NodeType.WORKFLOW_STEP,
                name=workflow,
                properties={
                    "workflow_type": workflow.lower().replace(" ", "_"),
                    "stage_count": 7,  # 企業版7階段
                    "mcp_components": await self._get_workflow_mcps(workflow)
                },
                metadata={"index": i}
            )
            await self.engine.add_node(graph_id, node)
        
        # 添加MCP組件節點
        mcp_components = [
            "MermaidFlow MCP",
            "ag-ui MCP", 
            "stagewise MCP",
            "test MCP",
            "SmartUI MCP",
            "DeepGraph MCP"  # 新增
        ]
        
        for mcp in mcp_components:
            node = GraphNode(
                id=f"mcp_{mcp.lower().replace(' ', '_')}",
                type=NodeType.COMPONENT,
                name=mcp,
                properties={
                    "component_type": "mcp",
                    "capabilities": await self._get_mcp_capabilities(mcp)
                },
                metadata={"category": "mcp"}
            )
            await self.engine.add_node(graph_id, node)
        
        # 構建連接關係
        await self._build_workflow_connections(graph_id)
        
        # 分析圖
        result = await self.engine.analyze_graph(graph_id)
        print(f"✅ 工作流圖構建完成: {result.nodes_count} 節點, {result.edges_count} 邊")
        
        return result
    
    async def _get_workflow_mcps(self, workflow: str) -> List[str]:
        """獲取工作流相關的MCP組件"""
        mapping = {
            "Code Generation": ["MermaidFlow MCP", "DeepGraph MCP"],
            "UI Design": ["ag-ui MCP", "SmartUI MCP", "DeepGraph MCP"],
            "API Development": ["stagewise MCP", "test MCP", "DeepGraph MCP"],
            "Database Design": ["MermaidFlow MCP", "DeepGraph MCP"],
            "Testing Automation": ["test MCP", "stagewise MCP", "DeepGraph MCP"],
            "Deployment Pipeline": ["DeepGraph MCP"]
        }
        return mapping.get(workflow, ["DeepGraph MCP"])
    
    async def _get_mcp_capabilities(self, mcp: str) -> List[str]:
        """獲取MCP組件能力"""
        capabilities = {
            "MermaidFlow MCP": ["流程設計", "業務建模", "可視化"],
            "ag-ui MCP": ["UI組件生成", "拖拽設計", "響應式佈局"],
            "stagewise MCP": ["操作錄製", "回放測試", "階段管理"],
            "test MCP": ["測試管理", "自動化執行", "報告生成"],
            "SmartUI MCP": ["AI UI生成", "智能優化", "無障礙增強"],
            "DeepGraph MCP": ["圖分析", "依賴洞察", "優化建議"]
        }
        return capabilities.get(mcp, [])
    
    async def _build_workflow_connections(self, graph_id: str) -> None:
        """構建工作流連接"""
        # 工作流之間的依賴關係
        workflow_deps = [
            ("workflow_0", "workflow_1", "feeds_into"),  # Code Gen -> UI Design
            ("workflow_1", "workflow_2", "feeds_into"),  # UI Design -> API Dev
            ("workflow_2", "workflow_3", "feeds_into"),  # API Dev -> DB Design
            ("workflow_0", "workflow_4", "tested_by"),   # Code Gen -> Testing
            ("workflow_1", "workflow_4", "tested_by"),   # UI Design -> Testing
            ("workflow_4", "workflow_5", "feeds_into"),  # Testing -> Deployment
        ]
        
        for source, target, relationship in workflow_deps:
            edge = GraphEdge(source=source, target=target, relationship=relationship)
            await self.engine.add_edge(graph_id, edge)
        
        # MCP與工作流的連接
        mcp_workflow_connections = [
            ("mcp_mermaidflow_mcp", "workflow_0", "supports"),
            ("mcp_ag-ui_mcp", "workflow_1", "supports"),
            ("mcp_smartui_mcp", "workflow_1", "supports"),
            ("mcp_stagewise_mcp", "workflow_2", "supports"),
            ("mcp_test_mcp", "workflow_4", "supports"),
            ("mcp_deepgraph_mcp", "workflow_0", "supports"),
            ("mcp_deepgraph_mcp", "workflow_1", "supports"),
            ("mcp_deepgraph_mcp", "workflow_2", "supports"),
            ("mcp_deepgraph_mcp", "workflow_4", "supports"),
        ]
        
        for source, target, relationship in mcp_workflow_connections:
            edge = GraphEdge(source=source, target=target, relationship=relationship)
            await self.engine.add_edge(graph_id, edge)

# 導出主類
__all__ = [
    'DeepGraphEngine',
    'CodeGraphBuilder', 
    'WorkflowGraphBuilder',
    'GraphNode',
    'GraphEdge',
    'GraphAnalysisResult',
    'GraphType',
    'NodeType'
]

if __name__ == "__main__":
    async def demo():
        """演示DeepGraph MCP"""
        print("🚀 DeepGraph MCP 演示開始")
        
        # 初始化引擎
        engine = DeepGraphEngine()
        code_builder = CodeGraphBuilder(engine)
        workflow_builder = WorkflowGraphBuilder(engine)
        
        # 構建代碼圖
        current_dir = os.path.dirname(os.path.abspath(__file__))
        code_result = await code_builder.build_from_directory(current_dir, "code_graph")
        
        print(f"\n📊 代碼圖分析結果:")
        print(f"節點數: {code_result.nodes_count}")
        print(f"邊數: {code_result.edges_count}")
        print(f"洞察: {code_result.insights}")
        print(f"建議: {code_result.recommendations}")
        
        # 構建工作流圖
        workflow_result = await workflow_builder.build_codeflow_graph("workflow_graph", {})
        
        print(f"\n🔄 工作流圖分析結果:")
        print(f"節點數: {workflow_result.nodes_count}")
        print(f"邊數: {workflow_result.edges_count}")
        print(f"洞察: {workflow_result.insights}")
        print(f"建議: {workflow_result.recommendations}")
        
        print("\n✅ DeepGraph MCP 演示完成")
    
    # 運行演示
    asyncio.run(demo())