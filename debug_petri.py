import asyncio
from laap.orchestration.dsl import act, compile_workflow, seq
from laap.orchestration.kernel import OrchestrationKernel
from laap.orchestration.actor import ActorSystem
from laap.tools.base import ToolResult
from laap.tools.tool_registry import TOOL_REGISTRY, _register


def mock_read(path):
    return ToolResult(success=True, output=f"read {path}")


def mock_search(pattern, root=".", glob="*.py", max_results=20):
    return [{"snippet": f"search {pattern}"}]


async def main():
    _register("read_file", mock_read, "filesystem", "", overwrite=True)
    _register("search_files", mock_search, "search", "", overwrite=True)

    system = ActorSystem("debug")
    workflow = seq(
        act("read_file", {"path": "x"}, output_key="file_content"),
        act("search_files", {"pattern": "y"}, output_key="search_hits"),
    )
    from laap.body import create_default_body_system
    body_system = create_default_body_system()
    net, bindings, outputs = compile_workflow(workflow, actor_system=system, tool_registry=body_system.tools)
    print("places:", list(net.places.keys()))
    print("transitions:", list(net.transitions.keys()))
    print("initial tokens:")
    for pid, place in net.places.items():
        if place.tokens:
            print(f"  {pid}: {place.tokens}")
    print("bindings:", bindings)
    print("outputs:", outputs)

    kernel = OrchestrationKernel(system, net)
    for tid, aids in bindings.items():
        for aid in aids:
            kernel.bind_transition(tid, aid)
    await kernel.run()

    print("\nafter run:")
    for pid, place in net.places.items():
        if place.tokens:
            print(f"  {pid}: {place.tokens}")
    print("execution log:", len(net.execution_log))
    for entry in net.execution_log:
        print(f"  {entry['transition_id']}: produced {entry['produced'].keys()}")

    await system.stop_all()


if __name__ == "__main__":
    asyncio.run(main())
