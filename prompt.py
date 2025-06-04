dad_prompt = """
For the stock with this ticker: '{stock}', answer the following questions with the most recent up-to-date information to the best of your ability. Separate your answer by new lines.

- What is the current stock price?"
- What is the price-earnings ratio? Provide just the number.
- What is the current dividend? Provide just the number as a percentage.
- What is the 52-week high and low? Format your output exactly like this: "<52-week high>, <52-week low>"
- Has there been insider buying in the last 6 months? Provide "yes" or "no".
"""

suggestion_prompt = """
Consider the company with this ticker: {ticker}.
Here is a filtered covered call options chain for this company:

{options_chain}

Additionally, here are the stock fundamentals for this company:

{stock_fundamentals}

With this information, pick the best 2 to 3 contracts to sell based on delta, premium, and time to expiration. 
Make your decisions using this strategy: {stragety}.
Make sure you show the total direct profits (NOT per share!) that could be made by your suggested contracts, considering the current market price of the stock as a loss (if contract strikes out) and the premium + strike payment as a gain.
Please re-iterate the fundamentals at the beginning of your response, and your final suggestions in table format at the end.
Explain your reasoning in plain English.
"""

suggestion_prompt2 = """
You are given the following data for the company with ticker: {ticker}.

== FILTERED COVERED CALL OPTIONS CHAIN ==
{options_chain}

== STOCK FUNDAMENTALS ==
{stock_fundamentals}

Using this data, apply the following covered call selection strategy:
{stragety}

### TASK ###
1. Stock Fundamentals Summary  
   - Summarize the key fundamentals at the beginning of your response under a section titled **"Stock Fundamentals Summary"**. Use bullet points or a short paragraph.

2. Reasoning  
   - Explain in plain English why you selected each contract. Reference relevant metrics such as premium, time to expiration, and risk/reward.

3. Final Contract Suggestions (Table Format)  
   - Recommend the **best 2 to 3 contracts to sell**.  
   - Calculate **Total Direct Profit** using the following fixed formula:

     **Total Direct Profit = (Premium × 100) + (Strike Price − Current Market Price) × 100**

     - If the strike price is **below** the current market price, that difference is a loss.
     - If the strike price is **above** the market price, that difference is a gain.
     - Always assume the stock is called away at expiration.

   - Display the results in a table with **exactly the following format and columns**:

    | Expiration Date | Strike Price | Premium | Total Direct Profit ($) |
    |------------------|--------------|---------|--------------------------|
    |                  |              |         |                          |
    |                  |              |         |                          |

   - Include the table in all responses, even if only two contracts are recommended.
   - Maintain the same number, order, and labeling of columns in every output.

All responses must strictly follow the structure and formatting specified above.
"""