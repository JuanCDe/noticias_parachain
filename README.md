# Parachains_news
Telegram bot to replicate tweets from selected users (parachains official accounts)

## Configuración config.yml
tg_config:  
&nbsp;&nbsp;&nbsp;&nbsp; bot_token: str. "Telegram bot token. Given by BotFather"  
&nbsp;&nbsp;&nbsp;&nbsp; chat_id: int. "Telegram group id"  
&nbsp;&nbsp;&nbsp;&nbsp; dev_chat_id: int. "Debugging purposes"  
tw_config:  
&nbsp;&nbsp;&nbsp;&nbsp; bearer_token: str. "Twitter dev token"  
&nbsp;&nbsp;&nbsp;&nbsp;  handles:  
&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; - list  
&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; - of  
&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; - twitter  
&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; - handles  