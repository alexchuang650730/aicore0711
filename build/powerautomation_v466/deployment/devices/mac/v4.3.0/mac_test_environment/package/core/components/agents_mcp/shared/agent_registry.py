"""
Agent Registry - 智能体注册管理
"""

class AgentRegistry:
    """智能体注册表"""
    
    def __init__(self):
        self.agents = {}
    
    def register_agent(self, agent_id, agent):
        """注册智能体"""
        self.agents[agent_id] = agent
    
    def get_agent(self, agent_id):
        """获取智能体"""
        return self.agents.get(agent_id)

