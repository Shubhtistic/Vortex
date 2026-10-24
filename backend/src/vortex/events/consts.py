# asyncpg caps each query at 32,767 bind arguments. The events table currently
# has 21 columns, so 1,500 rows use at most 31,500 arguments per INSERT.
EVENTS_INSERT_CHUNK_SIZE = 1500

# reserved event names the ingestion service branches on
IDENTIFY_EVENT_NAME = "$identify"
GROUP_IDENTIFY_EVENT_NAME = "$group_identify"
