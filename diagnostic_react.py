from llama_index.core.agent import ReActAgent
import inspect

print(f"ReActAgent attributes: {dir(ReActAgent)}")
print(f"ReActAgent from_tools in attributes: {'from_tools' in dir(ReActAgent)}")

try:
    source = inspect.getsource(ReActAgent)
    print("\nReActAgent Source Snippet:")
    print(source[:500])
except:
    print("Could not get source")
