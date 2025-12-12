version 1.0 - release 
 + added a discord objects parser for json payloads
 + added a message handler (inherited from 'discord_object')
 + added an HTTP error code handler across the handlers
 + ^ added the exceptions related to the http codes at '_core/exceptions.py'
 + added a factory method for fetching channels !(WebSocket_Handler.get_channel())
 + added a factory method for fetching messages !(channel_base_handler.get_message())
 + improved typing support across the board
 + improved the shards startup speed ?(the slowness was due to each shard having to fetch the gatway url and bot info)
 + improved the overall project's type support
 + added the Black python formatter to the project