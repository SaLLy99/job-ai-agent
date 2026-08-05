import sqlite3

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from graph.state import AgentState

from graph.nodes import (
    understand_query,
    scrape_jobs,
    validate_jobs,
    enrich_jobs,
    deduplicate,
    filter_jobs,
    rank_jobs,
    verify_results,
    explain_jobs,
    save_memory
)


def create_workflow():

    builder = StateGraph(AgentState)

    # =========================
    # REGISTER NODES
    # =========================

    builder.add_node(
        "understand_query",
        understand_query
    )

    builder.add_node(
        "scrape_jobs",
        scrape_jobs
    )

    builder.add_node(
        "validate_jobs",
        validate_jobs
    )

    builder.add_node(
        "enrich_jobs",
        enrich_jobs
    )

    builder.add_node(
        "deduplicate",
        deduplicate
    )

    builder.add_node(
        "filter_jobs",
        filter_jobs
    )

    builder.add_node(
        "rank_jobs",
        rank_jobs
    )

    builder.add_node(
        "verify_results",
        verify_results
    )

    builder.add_node(
        "explain_jobs",
        explain_jobs
    )

    builder.add_node(
        "save_memory",
        save_memory
    )

    # =========================
    # FLOW
    # =========================

    builder.set_entry_point(
        "understand_query"
    )

    builder.add_edge(
        "understand_query",
        "scrape_jobs"
    )

    builder.add_edge(
        "scrape_jobs",
        "validate_jobs"
    )

    builder.add_edge(
        "validate_jobs",
        "enrich_jobs"
    )

    builder.add_edge(
        "enrich_jobs",
        "deduplicate"
    )

    builder.add_edge(
        "deduplicate",
        "filter_jobs"
    )

    builder.add_edge(
        "filter_jobs",
        "rank_jobs"
    )

    builder.add_edge(
        "rank_jobs",
        "verify_results"
    )

    builder.add_edge(
        "verify_results",
        "explain_jobs"
    )

    builder.add_edge(
        "explain_jobs",
        "save_memory"
    )

    builder.add_edge(
        "save_memory",
        END
    )

    # =========================
    # SQLITE CHECKPOINTER
    # =========================

    conn = sqlite3.connect("agent.db", check_same_thread=False)
    memory = SqliteSaver(conn)

    # =========================
    # COMPILE
    # =========================

    graph = builder.compile(
        checkpointer=memory
    )

    return graph
