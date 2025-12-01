# test_llm.py
from src import llm_client

if __name__ == "__main__":
    print("Running debug_run('Say hello') ...")
    out = llm_client.debug_run("Say hello", max_output_tokens=512)
    import pprint; pprint.pprint(out)
