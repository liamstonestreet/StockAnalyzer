from llm import stock_analysis_prompt, suggestion_prompt
import llm
import options


def main():
	pass

def test():
	expert = llm.LLM()
	# 1: Load & filter options
	chain = options.get_mock_options_chain()
	filtered = options.filter_conservative_calls(chain)
	prompt = suggestion_prompt.format(options_chain=filtered.to_string(index=False))
	# 2: Get LLM output
	response = expert.ask(prompt)
	print("\n=== LLM Suggestion ===")
	print(response)


if __name__ == "__main__":
	test()
	# main()