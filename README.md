    # chat_bot_ISS

    Prototype chatbot that surfaces live ISS information via public APIs.

    ## Architecture
    - Data fetch: polls an ISS location API for latitude/longitude and metadata.
    - Bot logic: simple intent parsing to answer “where is the ISS?” or similar queries.
    - Interface: CLI or lightweight web/Node entrypoint (check repo files).

    ## Setup & Run
    - Requires Node.js. If a package.json exists, run `npm install` then the documented start script; otherwise run the main JS file with `node`.

    ## Notes
    - External API calls require network; handle rate limits and failures gracefully.
    - Consider caching the last position to avoid hammering the API on repeated queries.

    ## Author
    Oualid Obbad (@oualidobbad)