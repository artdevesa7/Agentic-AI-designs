"""
AI Agent Blueprint with LangGraph - 4 Pattern Designs
=====================================================

This blueprint demonstrates:
1. ReAct Pattern - Reasoning + Action with tool use
2. Plan-Execute Pattern - Strategic planning with execution
3. Self-Reflection Pattern - Iterative refinement with critique
4. Adaptive Multi-Agent Pattern - Dynamic agent collaboration

Features:
- Planning: Strategic goal decomposition
- Adaptation: Dynamic strategy adjustment
- Autonomy: Independent decision-making
- Self-reflection: Quality assessment and iteration
"""

from typing import TypedDict, Annotated, Sequence, Literal
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
import operator
import requests
import json
from datetime import datetime, timedelta
import numpy as np


# ============================================================================
# TOOLS - Stock APIs and Vector Database
# ============================================================================

@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch current stock price from Alpha Vantage API.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
    
    Returns:
        Dictionary with price, volume, and timestamp
    """
    # Mock implementation - replace with actual API
    api_key = "YOUR_ALPHA_VANTAGE_KEY"
    # url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
    
    # Mock data for demonstration
    mock_data = {
        "symbol": symbol,
        "price": np.random.uniform(100, 500),
        "volume": np.random.randint(1000000, 10000000),
        "change_percent": np.random.uniform(-5, 5),
        "timestamp": datetime.now().isoformat()
    }
    return mock_data


@tool
def get_stock_history(symbol: str, days: int = 30) -> dict:
    """
    Fetch historical stock data from Financial Modeling Prep API.
    
    Args:
        symbol: Stock ticker symbol
        days: Number of days of historical data
    
    Returns:
        Dictionary with historical prices and analysis
    """
    # Mock implementation
    api_key = "YOUR_FMP_KEY"
    # url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={api_key}"
    
    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    prices = [np.random.uniform(90, 510) for _ in range(days)]
    
    return {
        "symbol": symbol,
        "dates": dates[:5],  # First 5 for brevity
        "prices": prices[:5],
        "avg_price": np.mean(prices),
        "volatility": np.std(prices),
        "trend": "bullish" if prices[-1] > prices[0] else "bearish"
    }


@tool
def vector_db_search(query: str, top_k: int = 5) -> dict:
    """
    Search vector database for similar stock analysis reports and news.
    Uses semantic similarity search.
    
    Args:
        query: Search query
        top_k: Number of results to return
    
    Returns:
        Dictionary with relevant documents and similarity scores
    """
    # Mock implementation - replace with actual vector DB (Pinecone, Weaviate, etc.)
    mock_results = [
        {
            "content": f"Analysis report on tech stocks showing strong performance in Q4",
            "similarity": 0.92,
            "source": "MarketWatch",
            "date": "2025-12-15"
        },
        {
            "content": f"AI sector stocks recommended for long-term growth",
            "similarity": 0.87,
            "source": "Bloomberg",
            "date": "2025-12-10"
        },
        {
            "content": f"Market volatility expected due to economic indicators",
            "similarity": 0.83,
            "source": "Reuters",
            "date": "2025-12-18"
        }
    ]
    return {
        "query": query,
        "results": mock_results[:top_k],
        "total_found": len(mock_results)
    }


# Tool list for agents
tools = [get_stock_price, get_stock_history, vector_db_search]
tool_node = ToolNode(tools)


# ============================================================================
# PATTERN 1: ReAct Pattern (Reasoning + Action)
# ============================================================================

class ReActState(TypedDict):
    """State for ReAct pattern - iterative reasoning and action"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    iteration: int
    max_iterations: int


def create_react_agent():
    """ReAct pattern: Think, Act, Observe loop"""
    
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
    llm_with_tools = llm.bind_tools(tools)
    
    def reasoning_node(state: ReActState):
        """Agent reasons about what to do next"""
        system_prompt = SystemMessage(content="""You are a financial analyst agent using ReAct pattern.
        
Think step-by-step:
1. Observe the current situation
2. Reason about what information you need
3. Decide which tool to use
4. After tool results, synthesize insights

Be concise and focused.""")
        
        messages = [system_prompt] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response], "iteration": state["iteration"] + 1}
    
    def should_continue(state: ReActState) -> Literal["tools", "end"]:
        """Decide whether to continue or end"""
        messages = state["messages"]
        last_message = messages[-1]
        
        # Check iteration limit
        if state["iteration"] >= state["max_iterations"]:
            return "end"
        
        # If tool calls exist, continue
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        
        return "end"
    
    # Build graph
    workflow = StateGraph(ReActState)
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("tools", tool_node)
    
    workflow.add_edge(START, "reasoning")
    workflow.add_conditional_edges("reasoning", should_continue, {"tools": "tools", "end": END})
    workflow.add_edge("tools", "reasoning")
    
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# ============================================================================
# PATTERN 2: Plan-Execute Pattern
# ============================================================================

class PlanExecuteState(TypedDict):
    """State for Plan-Execute pattern"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    plan: list[str]
    completed_steps: list[str]
    current_step: int
    results: dict


def create_plan_execute_agent():
    """Plan-Execute pattern: Strategic planning then execution"""
    
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
    llm_with_tools = llm.bind_tools(tools)
    
    def planner_node(state: PlanExecuteState):
        """Create a strategic plan"""
        system_prompt = """You are a strategic planning agent for financial analysis.

Given a user query, create a detailed step-by-step plan.
Each step should be specific and actionable.
Return ONLY a numbered list of steps, nothing else.

Example:
1. Get current stock price for AAPL
2. Retrieve 30-day historical data
3. Search vector DB for recent AAPL analysis
4. Synthesize findings into recommendation"""
        
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = llm.invoke(messages)
        
        # Parse plan from response
        plan_text = response.content
        plan_steps = [line.strip() for line in plan_text.split('\n') if line.strip() and line[0].isdigit()]
        
        return {
            "plan": plan_steps,
            "current_step": 0,
            "results": {},
            "messages": [AIMessage(content=f"Created plan with {len(plan_steps)} steps")]
        }
    
    def executor_node(state: PlanExecuteState):
        """Execute current step of the plan"""
        current_step = state["current_step"]
        
        if current_step >= len(state["plan"]):
            return {"messages": [AIMessage(content="All steps completed")]}
        
        step_description = state["plan"][current_step]
        
        system_prompt = f"""You are executing step {current_step + 1} of the plan:
"{step_description}"

Use the appropriate tools to complete this step. Be focused and efficient."""
        
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=step_description)]
        response = llm_with_tools.invoke(messages)
        
        return {
            "messages": [response],
            "current_step": current_step + 1
        }
    
    def should_continue(state: PlanExecuteState) -> Literal["execute", "synthesize", "tools"]:
        """Route based on execution state"""
        last_message = state["messages"][-1]
        
        # If we have tool calls, execute them
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        
        # If all steps complete, synthesize
        if state["current_step"] >= len(state["plan"]):
            return "synthesize"
        
        # Otherwise, continue executing
        return "execute"
    
    def synthesizer_node(state: PlanExecuteState):
        """Synthesize all results into final answer"""
        system_prompt = """Review all the steps executed and their results.
Provide a comprehensive synthesis and recommendation based on the findings."""
        
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = llm.invoke(messages)
        return {"messages": [response]}
    
    # Build graph
    workflow = StateGraph(PlanExecuteState)
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("synthesizer", synthesizer_node)
    
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_conditional_edges(
        "executor",
        should_continue,
        {"execute": "executor", "tools": "tools", "synthesize": "synthesizer"}
    )
    workflow.add_edge("tools", "executor")
    workflow.add_edge("synthesizer", END)
    
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# ============================================================================
# PATTERN 3: Self-Reflection Pattern
# ============================================================================

class ReflectionState(TypedDict):
    """State for self-reflection pattern"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    draft: str
    critique: str
    iteration: int
    max_iterations: int
    quality_score: float


def create_reflection_agent():
    """Self-reflection pattern: Generate, critique, refine"""
    
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.3)
    llm_with_tools = llm.bind_tools(tools)
    
    def generator_node(state: ReflectionState):
        """Generate initial or refined analysis"""
        system_prompt = """You are a financial analyst creating stock analysis reports.
        
If this is a revision, incorporate the critique to improve your analysis.
Use tools to gather data, then create a comprehensive report."""
        
        context = ""
        if state.get("critique"):
            context = f"\n\nPrevious critique: {state['critique']}\nImprove based on this feedback."
        
        messages = [SystemMessage(content=system_prompt + context)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        
        return {"messages": [response], "iteration": state["iteration"] + 1}
    
    def critic_node(state: ReflectionState):
        """Critique the generated analysis"""
        last_message = state["messages"][-1]
        draft = last_message.content
        
        critique_prompt = f"""Review this stock analysis critically:

{draft}

Evaluate on:
1. Data accuracy and completeness (0-10)
2. Reasoning quality (0-10)
3. Actionability of recommendations (0-10)
4. Risk assessment thoroughness (0-10)

Provide:
- Overall quality score (average of above)
- Specific improvements needed
- What's missing or unclear

Format:
SCORE: X.X/10
CRITIQUE: [detailed feedback]"""
        
        messages = [SystemMessage(content="You are a critical reviewer of financial analysis."),
                   HumanMessage(content=critique_prompt)]
        response = llm.invoke(messages)
        
        # Parse score
        content = response.content
        score = 7.5  # default
        if "SCORE:" in content:
            try:
                score_str = content.split("SCORE:")[1].split("/")[0].strip()
                score = float(score_str)
            except:
                pass
        
        return {
            "critique": content,
            "quality_score": score,
            "messages": [response]
        }
    
    def should_continue(state: ReflectionState) -> Literal["generate", "tools", "end"]:
        """Decide whether to refine further"""
        last_message = state["messages"][-1]
        
        # Execute tools if needed
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        
        # End if quality is good or max iterations reached
        if state["quality_score"] >= 8.5 or state["iteration"] >= state["max_iterations"]:
            return "end"
        
        return "generate"
    
    # Build graph
    workflow = StateGraph(ReflectionState)
    workflow.add_node("generator", generator_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("tools", tool_node)
    
    workflow.add_edge(START, "generator")
    workflow.add_conditional_edges(
        "generator",
        should_continue,
        {"generate": "critic", "tools": "tools", "end": END}
    )
    workflow.add_edge("tools", "generator")
    workflow.add_edge("critic", "generator")
    
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# ============================================================================
# PATTERN 4: Adaptive Multi-Agent Pattern
# ============================================================================

class MultiAgentState(TypedDict):
    """State for multi-agent collaboration"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str
    completed_agents: list[str]
    findings: dict
    confidence: float


def create_multi_agent_system():
    """Adaptive multi-agent: Specialized agents collaborate dynamically"""
    
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
    llm_with_tools = llm.bind_tools(tools)
    
    def supervisor_node(state: MultiAgentState):
        """Supervisor decides which agent to invoke next"""
        system_prompt = """You are a supervisor coordinating financial analysis agents.

Available agents:
- data_collector: Gathers stock data and metrics
- technical_analyst: Performs technical analysis on price patterns
- research_analyst: Reviews market research and news
- risk_assessor: Evaluates risks and uncertainties
- synthesizer: Creates final recommendation

Based on the task and what's been completed, decide the next agent.
Respond with ONLY the agent name, nothing else."""
        
        completed = state.get("completed_agents", [])
        findings_summary = "\n".join([f"- {k}: {v}" for k, v in state.get("findings", {}).items()])
        
        context = f"""
Completed agents: {completed}
Current findings:
{findings_summary}

What agent should work next?"""
        
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=context)]
        response = llm.invoke(messages)
        
        next_agent = response.content.strip().lower()
        
        # Validation
        valid_agents = ["data_collector", "technical_analyst", "research_analyst", 
                       "risk_assessor", "synthesizer"]
        if next_agent not in valid_agents:
            next_agent = "data_collector"
        
        return {"next_agent": next_agent, "messages": [response]}
    
    def data_collector_node(state: MultiAgentState):
        """Collects raw stock data"""
        system_prompt = """You are a data collection specialist.
Gather current price, historical data for the requested stocks.
Be thorough and systematic."""
        
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        
        completed = state.get("completed_agents", [])
        completed.append("data_collector")
        
        findings = state.get("findings", {})
        findings["data_collection"] = "Stock data gathered"
        
        return {
            "messages": [response],
            "completed_agents": completed,
            "findings": findings
        }
    
    def technical_analyst_node(state: MultiAgentState):
        """Performs technical analysis"""
        system_prompt = """You are a technical analysis expert.
Analyze price trends, volatility, momentum.
Identify support/resistance levels and patterns."""
        
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = llm.invoke(messages)
        
        completed = state.get("completed_agents", [])
        completed.append("technical_analyst")
        
        findings = state.get("findings", {})
        findings["technical_analysis"] = "Pattern analysis complete"
        
        return {
            "messages": [response],
            "completed_agents": completed,
            "findings": findings
        }
    
    def research_analyst_node(state: MultiAgentState):
        """Reviews market research"""
        system_prompt = """You are a market research specialist.
Search for relevant news, analyst reports, market sentiment.
Provide context and qualitative insights."""
        
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        
        completed = state.get("completed_agents", [])
        completed.append("research_analyst")
        
        findings = state.get("findings", {})
        findings["research"] = "Market context analyzed"
        
        return {
            "messages": [response],
            "completed_agents": completed,
            "findings": findings
        }
    
    def risk_assessor_node(state: MultiAgentState):
        """Assesses risks"""
        system_prompt = """You are a risk assessment expert.
Evaluate volatility, market risks, company-specific risks.
Quantify uncertainty and provide risk rating."""
        
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = llm.invoke(messages)
        
        completed = state.get("completed_agents", [])
        completed.append("risk_assessor")
        
        findings = state.get("findings", {})
        findings["risk_assessment"] = "Risks evaluated"
        
        confidence = np.random.uniform(0.6, 0.95)  # Mock confidence
        
        return {
            "messages": [response],
            "completed_agents": completed,
            "findings": findings,
            "confidence": confidence
        }
    
    def synthesizer_node(state: MultiAgentState):
        """Creates final synthesis"""
        system_prompt = """You are the synthesis specialist.
Review ALL findings from other agents.
Create a comprehensive, actionable recommendation.
Include confidence level and key risks."""
        
        findings_text = "\n".join([f"{k}: {v}" for k, v in state.get("findings", {}).items()])
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Agent findings:\n{findings_text}")
        ] + state["messages"]
        
        response = llm.invoke(messages)
        
        completed = state.get("completed_agents", [])
        completed.append("synthesizer")
        
        return {
            "messages": [response],
            "completed_agents": completed
        }
    
    def route_to_agent(state: MultiAgentState) -> str:
        """Route to the next agent"""
        next_agent = state.get("next_agent", "supervisor")
        
        # Check if we have tool calls to execute
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        
        # If synthesizer is done, end
        if "synthesizer" in state.get("completed_agents", []):
            return "end"
        
        return next_agent
    
    # Build graph
    workflow = StateGraph(MultiAgentState)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("data_collector", data_collector_node)
    workflow.add_node("technical_analyst", technical_analyst_node)
    workflow.add_node("research_analyst", research_analyst_node)
    workflow.add_node("risk_assessor", risk_assessor_node)
    workflow.add_node("synthesizer", synthesizer_node)
    workflow.add_node("tools", tool_node)
    
    workflow.add_edge(START, "supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "data_collector": "data_collector",
            "technical_analyst": "technical_analyst",
            "research_analyst": "research_analyst",
            "risk_assessor": "risk_assessor",
            "synthesizer": "synthesizer",
            "tools": "tools",
            "end": END
        }
    )
    
    # All specialist agents return to supervisor
    for agent in ["data_collector", "technical_analyst", "research_analyst", 
                  "risk_assessor", "synthesizer"]:
        workflow.add_conditional_edges(
            agent,
            route_to_agent,
            {
                "supervisor": "supervisor",
                "tools": "tools",
                "end": END
            }
        )
    
    workflow.add_edge("tools", "supervisor")
    
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# ============================================================================
# DEMO EXECUTION
# ============================================================================

def demo_agents():
    """Demonstrate all 4 agent patterns"""
    
    print("=" * 80)
    print("AI AGENT BLUEPRINT - 4 PATTERN DEMONSTRATION")
    print("=" * 80)
    
    query = "Should I invest in AAPL? Analyze the stock."
    
    # Pattern 1: ReAct
    print("\n\n[PATTERN 1: ReAct - Reasoning + Action]")
    print("-" * 80)
    react_agent = create_react_agent()
    state = {
        "messages": [HumanMessage(content=query)],
        "iteration": 0,
        "max_iterations": 3
    }
    config = {"configurable": {"thread_id": "react-demo"}}
    result = react_agent.invoke(state, config)
    print(f"Final message: {result['messages'][-1].content[:200]}...")
    
    # Pattern 2: Plan-Execute
    print("\n\n[PATTERN 2: Plan-Execute - Strategic Planning]")
    print("-" * 80)
    plan_agent = create_plan_execute_agent()
    state = {
        "messages": [HumanMessage(content=query)],
        "plan": [],
        "completed_steps": [],
        "current_step": 0,
        "results": {}
    }
    config = {"configurable": {"thread_id": "plan-demo"}}
    result = plan_agent.invoke(state, config)
    print(f"Plan: {result.get('plan', [])}")
    print(f"Final message: {result['messages'][-1].content[:200]}...")
    
    # Pattern 3: Self-Reflection
    print("\n\n[PATTERN 3: Self-Reflection - Iterative Refinement]")
    print("-" * 80)
    reflection_agent = create_reflection_agent()
    state = {
        "messages": [HumanMessage(content=query)],
        "draft": "",
        "critique": "",
        "iteration": 0,
        "max_iterations": 2,
        "quality_score": 0.0
    }
    config = {"configurable": {"thread_id": "reflect-demo"}}
    result = reflection_agent.invoke(state, config)
    print(f"Quality score: {result.get('quality_score', 0)}/10")
    print(f"Final message: {result['messages'][-1].content[:200]}...")
    
    # Pattern 4: Multi-Agent
    print("\n\n[PATTERN 4: Adaptive Multi-Agent - Collaborative Specialists]")
    print("-" * 80)
    multi_agent = create_multi_agent_system()
    state = {
        "messages": [HumanMessage(content=query)],
        "next_agent": "supervisor",
        "completed_agents": [],
        "findings": {},
        "confidence": 0.0
    }
    config = {"configurable": {"thread_id": "multi-demo"}}
    result = multi_agent.invoke(state, config)
    print(f"Agents used: {result.get('completed_agents', [])}")
    print(f"Confidence: {result.get('confidence', 0):.2f}")
    print(f"Final message: {result['messages'][-1].content[:200]}...")
    
    print("\n\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    demo_agents()
