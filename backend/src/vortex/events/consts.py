# postgres 65,535 params limit ÷ event table 21 columns -> 3210 (approx)
EVENTS_INSERT_CHUNK_SIZE = 2500

# reserved event names the ingestion service branches on
IDENTIFY_EVENT_NAME = "$identify"
GROUP_IDENTIFY_EVENT_NAME = "$group_identify"
