#加载用户配置

import yaml
import os
from typing import Dict,Any

class ConfigLoader:
    def __init__(self,config_path:str="config.yaml"):
        self.config_path = config_path
        self.config_data=self._load()

    def _load(self)->Dict[str,Any]:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found at {self.config_path}")

        with open(self.config_path,"r",encoding="utf-8") as f:
            return yaml.safe_load(f)

    @property
    def llm_config(self)->Dict[str,Any]:
        return self.config_data.get("llm",{})

    @property
    def agent_config(self) -> Dict[str, Any]:
        return self.config_data.get("agent", {})


    def get(self, key: str, default: Any = None) -> Any:
        """
        让 ConfigLoader 支持类似字典的 get 操作
        """
        # 修改这里：将 self._config 改为 self.config_data
        return self.config_data.get(key, default)
