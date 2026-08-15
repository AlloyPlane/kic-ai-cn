#!/usr/bin/env python3
"""
Configuration Manager for KIC-AI
Handles saving and loading of API keys and settings
"""

import os
import json
import wx

class ConfigManager:
    """Manages configuration settings for KIC-AI"""
    
    def __init__(self):
        # Configuration file path
        self.config_dir = os.path.expanduser("~/.kic-ai")
        self.config_file = os.path.join(self.config_dir, "config.json")
        
        # Default configuration
        self.default_config = {
            "nexar_api_key": "",
            "ai_mode": "analysis",
            "language": "中文",
            "context_type": "pcb",
            "use_demo_mode": True,
            "pricing_providers": ["nexar"],
            "llm_provider": "deepseek",
            "llm_api_key": "",
            "llm_api_base": "",
            "llm_model": "",
            "websearch_enabled": True,
            "websearch_max_uses": 3,
            "websearch_model": "deepseek-v4-flash",
            "last_updated": ""
        }
        
        # Load existing config
        self.config = self.load_config()
    
    def ensure_config_dir(self):
        """Ensure configuration directory exists"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to handle missing keys
                    config = self.default_config.copy()
                    config.update(loaded_config)
                    return config
        except Exception as e:
            print(f"Error loading config: {e}")
        
        # Return default config if loading fails
        return self.default_config.copy()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            self.ensure_config_dir()
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
    
    def get_nexar_api_key(self):
        """Get Nexar API key (from config or environment)"""
        # Check config first
        api_key = self.config.get("nexar_api_key", "")
        if api_key:
            return api_key
        
        # Fallback to environment variable
        return os.getenv("NEXAR_TOKEN", "")
    
    def set_nexar_api_key(self, api_key):
        """Set Nexar API key"""
        self.config["nexar_api_key"] = api_key
        # Update demo mode based on whether we have an API key
        self.config["use_demo_mode"] = not bool(api_key.strip())
    
    def is_demo_mode(self):
        """Check if we're in demo mode"""
        return self.config.get("use_demo_mode", True) or not self.get_nexar_api_key()


class ConfigDialog(wx.Dialog):
    """Configuration dialog for KIC-AI settings"""
    
    def __init__(self, parent, config_manager):
        super().__init__(parent, title="KIC-AI Configuration", 
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
                         size=(540, 560))
        
        self.config_manager = config_manager
        self.ui_zh = (self.config_manager.get("language", "中文") == "中文")
        self.init_ui()
        self.load_current_settings()
    
    def tr(self, en, zh):
        """界面文本：中文为主，英文原样保留可对照"""
        return zh if self.ui_zh else en
    
    def on_scroll_resize(self, event):
        """内容超高时更新虚拟尺寸，出现竖向滚动条"""
        sizer = self.scroll.GetSizer()
        if sizer:
            self.scroll.SetVirtualSize(sizer.GetMinSize())
        event.Skip()
    
    def init_ui(self):
        """Initialize the user interface"""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title = wx.StaticText(panel, label=self.tr("🔧 KIC-AI Configuration", "🔧 KIC-AI 配置"))
        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        main_sizer.Add(title, 0, wx.ALL | wx.CENTER, 10)
        
        # 可滚动区域：内容超高时出现滚动条，避免控件被截断
        self.scroll = wx.ScrolledWindow(panel)
        self.scroll.SetScrollRate(10, 10)
        scroll_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Notebook for different sections
        notebook = wx.Notebook(self.scroll)
        
        # API Settings Tab
        api_panel = wx.Panel(notebook)
        self.create_api_panel(api_panel)
        notebook.AddPage(api_panel, self.tr("API Settings", "API 设置"))
        
        # General Settings Tab
        general_panel = wx.Panel(notebook)
        self.create_general_panel(general_panel)
        notebook.AddPage(general_panel, self.tr("General", "常规"))
        
        # Info Tab
        info_panel = wx.Panel(notebook)
        self.create_info_panel(info_panel)
        notebook.AddPage(info_panel, self.tr("Info", "关于"))
        
        scroll_sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 10)
        self.scroll.SetSizer(scroll_sizer)
        self.scroll.SetScrollRate(10, 10)
        self.scroll.EnableScrolling(False, True)
        self.scroll.Bind(wx.EVT_SIZE, self.on_scroll_resize)
        self.scroll.SetVirtualSize(scroll_sizer.GetMinSize())
        main_sizer.Add(self.scroll, 1, wx.EXPAND | wx.ALL, 5)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.test_btn = wx.Button(panel, label=self.tr("🧪 Test Connection", "🧪 测试连接"))
        self.save_btn = wx.Button(panel, wx.ID_OK, label=self.tr("💾 Save", "💾 保存"))
        self.cancel_btn = wx.Button(panel, wx.ID_CANCEL, label=self.tr("Cancel", "取消"))
        
        btn_sizer.Add(self.test_btn, 0, wx.RIGHT, 10)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(self.cancel_btn, 0, wx.RIGHT, 10)
        btn_sizer.Add(self.save_btn, 0)
        
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Bind events
        self.test_btn.Bind(wx.EVT_BUTTON, self.on_test_connection)
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save)
        
        panel.SetSizer(main_sizer)
    
    def create_api_panel(self, panel):
        """Create API settings panel"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Nexar API section
        nexar_box = wx.StaticBox(panel, label=self.tr("Nexar API Settings", "Nexar API 设置（元件价格）"))
        nexar_sizer = wx.StaticBoxSizer(nexar_box, wx.VERTICAL)
        
        # API Key input
        key_label = wx.StaticText(panel, label=self.tr("API Key:", "API 密钥："))
        self.api_key_ctrl = wx.TextCtrl(panel, style=wx.TE_PASSWORD, size=(300, -1))
        self.api_key_ctrl.SetHint(self.tr("Enter your Nexar API key (optional)", "输入你的 Nexar API 密钥（可选）"))
        
        # Demo mode checkbox
        self.demo_mode_cb = wx.CheckBox(panel, label=self.tr("Use demo mode (no API key required)", "使用演示模式（无需 API 密钥）"))
        
        # Status text
        self.status_text = wx.StaticText(panel, label="")
        
        # Help text
        help_text = wx.StaticText(panel, label=
            self.tr("• Leave empty to use demo mode with sample data\n• Get your free API key at: https://nexar.com/api\n• Demo mode provides realistic pricing for testing",
                    "• 留空则使用演示模式（示例数据）\n• 免费获取密钥：https://nexar.com/api\n• 演示模式提供真实感价格用于测试"))
        help_text.SetForegroundColour(wx.Colour(100, 100, 100))
        
        nexar_sizer.Add(key_label, 0, wx.ALL, 5)
        nexar_sizer.Add(self.api_key_ctrl, 0, wx.EXPAND | wx.ALL, 5)
        nexar_sizer.Add(self.demo_mode_cb, 0, wx.ALL, 5)
        nexar_sizer.Add(self.status_text, 0, wx.ALL, 5)
        nexar_sizer.Add(help_text, 0, wx.ALL, 5)
        
        sizer.Add(nexar_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # LLM (AI Model) section - 云端大模型 API 配置
        llm_box = wx.StaticBox(panel, label=self.tr("AI Model (LLM) - Cloud API", "AI 模型（LLM）- 云端 API"))
        llm_sizer = wx.StaticBoxSizer(llm_box, wx.VERTICAL)
        
        prov_label = wx.StaticText(panel, label=self.tr("Provider:", "供应商："))
        self.llm_provider_ctrl = wx.Choice(panel, choices=[
            "deepseek", "openai", "zhipu", "qwen", "minimax", "custom"])
        self.llm_provider_ctrl.SetSelection(0)
        
        key2_label = wx.StaticText(panel, label=self.tr("API Key:", "API 密钥："))
        self.llm_api_key_ctrl = wx.TextCtrl(panel, style=wx.TE_PASSWORD, size=(300, -1))
        self.llm_api_key_ctrl.SetHint(self.tr("Paste your API key (e.g. DeepSeek sk-...)", "粘贴你的 API 密钥（如 DeepSeek sk-...）"))
        
        base_label = wx.StaticText(panel, label=self.tr("Base URL (optional):", "接口地址（可选）："))
        self.llm_api_base_ctrl = wx.TextCtrl(panel, size=(300, -1))
        self.llm_api_base_ctrl.SetHint(self.tr("Leave empty for provider default, e.g. https://api.deepseek.com", "留空使用供应商默认地址，如 https://api.deepseek.com"))
        
        model_label = wx.StaticText(panel, label=self.tr("Model (optional):", "模型（可选）："))
        self.llm_model_ctrl = wx.TextCtrl(panel, size=(300, -1))
        self.llm_model_ctrl.SetHint(self.tr("Leave empty for provider default, e.g. deepseek-chat", "留空使用供应商默认模型，如 deepseek-chat"))
        
        llm_help = wx.StaticText(panel, label=
            self.tr("• Fill API Key to use cloud LLM (OpenAI-compatible API)\n• DeepSeek: https://api.deepseek.com  model: deepseek-chat\n• Leave API Key empty to fall back to local Ollama",
                    "• 填写 API 密钥即可使用云端大模型（OpenAI 兼容接口）\n• DeepSeek：https://api.deepseek.com  模型：deepseek-chat\n• API 密钥留空则回退到本地 Ollama"))
        llm_help.SetForegroundColour(wx.Colour(100, 100, 100))
        
        llm_sizer.Add(prov_label, 0, wx.ALL, 5)
        llm_sizer.Add(self.llm_provider_ctrl, 0, wx.EXPAND | wx.ALL, 5)
        llm_sizer.Add(key2_label, 0, wx.ALL, 5)
        llm_sizer.Add(self.llm_api_key_ctrl, 0, wx.EXPAND | wx.ALL, 5)
        llm_sizer.Add(base_label, 0, wx.ALL, 5)
        llm_sizer.Add(self.llm_api_base_ctrl, 0, wx.EXPAND | wx.ALL, 5)
        llm_sizer.Add(model_label, 0, wx.ALL, 5)
        llm_sizer.Add(self.llm_model_ctrl, 0, wx.EXPAND | wx.ALL, 5)
        llm_sizer.Add(llm_help, 0, wx.ALL, 5)
        
        sizer.Add(llm_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Web Search (联网搜索) section
        ws_box = wx.StaticBox(panel, label=self.tr("Web Search (DeepSeek native)", "联网搜索（DeepSeek 原生搜索）"))
        ws_sizer = wx.StaticBoxSizer(ws_box, wx.VERTICAL)
        self.ws_enable_cb = wx.CheckBox(panel, label=self.tr(
            "Enable web search before answering (triggered by keywords like 搜索/最新/今天)",
            "回答前自动联网搜索（消息含“搜索/最新/今天”等词时触发）"))
        self.ws_enable_cb.SetValue(True)
        max_label = wx.StaticText(panel, label=self.tr("Max searches per request (1-5):", "每次最多搜索次数（1-5）："))
        self.ws_max_ctrl = wx.SpinCtrl(panel, min=1, max=5, initial=3)
        model_label2 = wx.StaticText(panel, label=self.tr("Search model:", "搜索模型："))
        self.ws_model_ctrl = wx.TextCtrl(panel, size=(220, -1), value="deepseek-v4-flash")
        ws_help = wx.StaticText(panel, label=self.tr(
            "• Uses DeepSeek native web search (web_search_20250305, Anthropic-compatible API)\n"
            "• Requires a valid DeepSeek API Key (same as the AI Model above)\n"
            "• Results are shown in chat and injected into the answer context",
            "• 使用 DeepSeek 原生搜索（web_search_20250305，Anthropic 兼容接口）\n"
            "• 需要有效的 DeepSeek API 密钥（与上面 AI 模型共用）\n"
            "• 结果会显示在聊天区并注入回答上下文"))
        ws_help.SetForegroundColour(wx.Colour(100, 100, 100))
        ws_sizer.Add(self.ws_enable_cb, 0, wx.ALL, 5)
        ws_row = wx.BoxSizer(wx.HORIZONTAL)
        ws_row.Add(max_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        ws_row.Add(self.ws_max_ctrl, 0, wx.RIGHT, 15)
        ws_row.Add(model_label2, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        ws_row.Add(self.ws_model_ctrl, 0)
        ws_sizer.Add(ws_row, 0, wx.ALL, 5)
        ws_sizer.Add(ws_help, 0, wx.ALL, 5)
        sizer.Add(ws_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
    
    def create_general_panel(self, panel):
        """Create general settings panel"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Mode selection
        mode_box = wx.StaticBox(panel, label=self.tr("AI Mode", "AI 模式"))
        mode_sizer = wx.StaticBoxSizer(mode_box, wx.VERTICAL)
        
        self.mode_choice = wx.Choice(panel, choices=["analysis", "chat", "expert"])
        mode_sizer.Add(self.mode_choice, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(mode_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Language selection
        lang_box = wx.StaticBox(panel, label=self.tr("Language", "语言"))
        lang_sizer = wx.StaticBoxSizer(lang_box, wx.VERTICAL)
        
        self.lang_choice = wx.Choice(panel, choices=["中文", "English"])
        lang_sizer.Add(self.lang_choice, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(lang_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
    
    def create_info_panel(self, panel):
        """Create info panel"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        info_text = wx.StaticText(panel, label=
            self.tr("🔧 KIC-AI Assistant\n\nAn AI-powered assistant for KiCad PCB design.\n\nFeatures:\n• Component analysis and recommendations\n• Real-time pricing from multiple distributors\n• Design rule checking and suggestions\n• Multi-language support\n\nConfiguration:\n• Settings are saved to ~/.kic-ai/config.json\n• Environment variables are supported\n• Demo mode works without API keys\n\nNeed help? Check the documentation or report issues on GitHub.",
                    "🔧 KIC-AI 助手\n\n用于 KiCad PCB 设计的 AI 助手插件。\n\n功能：\n• 元器件分析与建议\n• 多家分销商实时价格查询\n• 设计规则检查与建议\n• 中英文界面（默认中文）\n\n配置：\n• 设置保存在 ~/.kic-ai/config.json\n• 支持环境变量\n• 演示模式无需 API 密钥\n\n需要帮助？请查看文档或在 GitHub 上反馈问题。"))
        
        sizer.Add(info_text, 1, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
    
    def load_current_settings(self):
        """Load current settings into the dialog"""
        # API key
        api_key = self.config_manager.get_nexar_api_key()
        self.api_key_ctrl.SetValue(api_key)
        
        # Demo mode
        demo_mode = self.config_manager.is_demo_mode()
        self.demo_mode_cb.SetValue(demo_mode)
        
        # AI mode
        ai_mode = self.config_manager.get("ai_mode", "analysis")
        mode_choices = ["analysis", "chat", "expert"]
        if ai_mode in mode_choices:
            self.mode_choice.SetSelection(mode_choices.index(ai_mode))
        
        # Language
        language = self.config_manager.get("language", "中文")
        lang_choices = ["中文", "English"]
        if language in lang_choices:
            self.lang_choice.SetSelection(lang_choices.index(language))
        
        # LLM settings
        provider = self.config_manager.get("llm_provider", "deepseek")
        providers = ["deepseek", "openai", "zhipu", "qwen", "minimax", "custom"]
        if provider in providers:
            self.llm_provider_ctrl.SetSelection(providers.index(provider))
        self.llm_api_key_ctrl.SetValue(self.config_manager.get("llm_api_key", ""))
        self.llm_api_base_ctrl.SetValue(self.config_manager.get("llm_api_base", ""))
        self.llm_model_ctrl.SetValue(self.config_manager.get("llm_model", ""))
        
        # Web search settings
        self.ws_enable_cb.SetValue(bool(self.config_manager.get("websearch_enabled", True)))
        self.ws_max_ctrl.SetValue(int(self.config_manager.get("websearch_max_uses", 3) or 3))
        self.ws_model_ctrl.SetValue(str(self.config_manager.get("websearch_model", "deepseek-v4-flash") or "deepseek-v4-flash"))
        
        # Update status
        self.update_status()
    
    def update_status(self):
        """Update the status text"""
        api_key = self.api_key_ctrl.GetValue().strip()
        if api_key:
            self.status_text.SetLabel(self.tr("✅ API key configured - Real Nexar API will be used", "✅ 已配置 API 密钥 - 将使用真实 Nexar API"))
            self.status_text.SetForegroundColour(wx.Colour(0, 128, 0))
        else:
            self.status_text.SetLabel(self.tr("ℹ️ Demo mode - Using sample pricing data", "ℹ️ 演示模式 - 使用示例价格数据"))
            self.status_text.SetForegroundColour(wx.Colour(0, 100, 200))
    
    def on_test_connection(self, event):
        """Test the API connection"""
        api_key = self.api_key_ctrl.GetValue().strip()
        
        if not api_key:
            wx.MessageBox(self.tr("No API key entered. Demo mode will be used.", "未输入 API 密钥，将使用演示模式。"),
                         "Test Result", wx.OK | wx.ICON_INFORMATION)
            return
        
        # Simple test - just check if key format looks valid
        if len(api_key) < 10:
            wx.MessageBox(self.tr("API key seems too short. Please check your key.", "API 密钥似乎太短，请检查。"),
                         "Test Result", wx.OK | wx.ICON_WARNING)
            return
        
        # For now, just show success (real API testing would require actual Nexar API call)
        wx.MessageBox(self.tr("API key format looks valid!\n\nNote: Actual connection testing requires implementing Nexar API authentication.",
                              "API 密钥格式看起来有效！\n\n注意：真正的连接测试需要实现 Nexar API 认证。"),
                     self.tr("Test Result", "测试结果"), wx.OK | wx.ICON_INFORMATION)
    
    def on_save(self, event):
        """Save the configuration"""
        try:
            # Save API key
            api_key = self.api_key_ctrl.GetValue().strip()
            self.config_manager.set_nexar_api_key(api_key)
            
            # Save AI mode
            mode_selection = self.mode_choice.GetSelection()
            if mode_selection != wx.NOT_FOUND:
                ai_mode = ["analysis", "chat", "expert"][mode_selection]
                self.config_manager.set("ai_mode", ai_mode)
            
            # Save language
            lang_selection = self.lang_choice.GetSelection()
            if lang_selection != wx.NOT_FOUND:
                language = ["中文", "English"][lang_selection]
                self.config_manager.set("language", language)
            
            # Save LLM settings
            prov_sel = self.llm_provider_ctrl.GetSelection()
            if prov_sel != wx.NOT_FOUND:
                self.config_manager.set("llm_provider", ["deepseek", "openai", "zhipu", "qwen", "minimax", "custom"][prov_sel])
            self.config_manager.set("llm_api_key", self.llm_api_key_ctrl.GetValue().strip())
            self.config_manager.set("llm_api_base", self.llm_api_base_ctrl.GetValue().strip())
            self.config_manager.set("llm_model", self.llm_model_ctrl.GetValue().strip())
            
            # Save web search settings
            self.config_manager.set("websearch_enabled", self.ws_enable_cb.GetValue())
            self.config_manager.set("websearch_max_uses", self.ws_max_ctrl.GetValue())
            self.config_manager.set("websearch_model", self.ws_model_ctrl.GetValue().strip() or "deepseek-v4-flash")
            
            # Save to file
            if self.config_manager.save_config():
                wx.MessageBox(self.tr("Configuration saved successfully!", "配置保存成功！"),
                             self.tr("Success", "成功"), wx.OK | wx.ICON_INFORMATION)
                self.EndModal(wx.ID_OK)
            else:
                wx.MessageBox(self.tr("Error saving configuration!", "保存配置出错！"),
                             self.tr("Error", "错误"), wx.OK | wx.ICON_ERROR)
        
        except Exception as e:
            wx.MessageBox(f"Error saving configuration: {str(e)}",
                         "Error", wx.OK | wx.ICON_ERROR)
