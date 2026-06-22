Table2Sch/
│
├── lib/                           
│   ├── platforms/                  # 【增强】存放 sts8300.yaml, v93000.yaml 等硬件描述
│   ├── sockets/                    
│   └── symbols/                    # 存放 Kelvin_Template.kicad_sch 等模板
│
├── src/                           
│   ├── main.py                     
│   ├── models/                    
│   │   └── schema.py               # Pydantic 数据模型
│   │
│   ├── platforms/                  # 【新增】多平台适配层 (Strategy Pattern)
│   │   ├── __init__.py             # 平台注册工厂 (PlatformFactory)
│   │   ├── base.py                 # 基类接口
│   │   ├── sts8300.py              # STS8300 专属调度与解析逻辑
│   │   └── v93000.py               # V93000 专属调度与解析逻辑
│   │
│   ├── parsers/                    # 输入解析层 (excel, sym)
│   ├── hw_modules/                 # 模板数据适配器 (把模型转为 @VAR@ 字典)
│   │
│   ├── core/                      
│   │   ├── scheduler.py            # 通用资源分配器 (可调用 platforms 里的特定规则)
│   │   └── checker.py              # 【增强】DRC 规则引擎，在生成前拦截拓扑错误
│   │
│   ├── gui/                        # 用户界面
│   │   ├── custom_widgets.py            # 
│   │   └── main_window.py              # 【增强】
│   │
│   └── exporters/                  
│       ├── kicad_api.py            # 纯粹的模板盖章引擎
│       ├── sch_generator.py        # 【业务组装】调 checker -> 调 API 盖章
│       └── report_gen.py