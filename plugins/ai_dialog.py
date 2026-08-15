# -*- coding: utf-8 -*-
import wx
import pcbnew
import threading
from datetime import datetime
import json
import logging
from config_manager import ConfigManager, ConfigDialog

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class AIAssistantDialog(wx.Frame):
    """AI Assistant Dialog voor PCB en Schematic design hulp met 3 interactie modi"""
    
    def __init__(self, parent, context_type="pcb"):
        # Set title based on context
        title = "KIC-AI Assistant - PCB" if context_type == "pcb" else "KIC-AI Assistant - Schematic"
        super().__init__(parent, title=title, size=(850, 650))
        
        self.context_type = context_type  # "pcb" or "schematic"
        
        # AI Interaction modes
        self.ANALYSIS_MODE = "analysis"      # Safe analysis and suggestions
        self.ADVISORY_MODE = "advisory"      # Step-by-step guidance with confirmation
        self.ASSISTANT_MODE = "assistant"    # Interactive recommendations (future: with actions)
        
        self.interaction_mode = self.ANALYSIS_MODE  # Default to safest mode
        # Language settings
        self.LANGUAGES = {
            0: {"code": "zh", "name": "中文"},
            1: {"code": "en", "name": "English"}
        }

        
        # Icon instellen (optioneel)
        self.SetIcon(wx.Icon())
        
        # Chat history voor context
        self.conversation_history = []
        
        # UI opzetten
        # Initialize configuration manager
        self.config_manager = ConfigManager()
        
        # Apply saved settings
        self.apply_saved_settings()
        
        self.init_ui()
        
        # Centreer op scherm
        self.CenterOnScreen()
        
        # Welcome message based on context
        if context_type == "schematic":
            welcome_msg = self._t(
                "Welcome to KIC-AI Assistant - Schematic Mode! 📋⚡\n\n"
                "I can help you with:\n"
                "• Schematic analysis and review\n"
                "• Circuit design advice\n"
                "• Component selection guidance\n"
                "• Net connectivity analysis\n"
                "• Symbol and annotation review\n\n"
                "🔧 Interaction Modes:\n"
                "• Analysis: Safe recommendations only\n"
                "• Advisory: Step-by-step guidance\n"
                "• Assistant: Interactive help (future automation)\n\n"
                "💡 I remember our conversation!\n"
                "Ask me about your circuit design!",
                "欢迎使用 KIC-AI 助手 - 原理图模式！📋⚡\n\n"
                "我可以帮你：\n"
                "• 原理图分析与审查\n"
                "• 电路设计建议\n"
                "• 器件选型指导\n"
                "• 网络连接分析\n"
                "• 符号与标注检查\n\n"
                "🔧 交互模式：\n"
                "• 分析模式：仅安全建议\n"
                "• 顾问模式：分步指导\n"
                "• 助手模式：交互式帮助\n\n"
                "💡 我会记住我们的对话！\n"
                "有什么电路设计问题尽管问我！")
        else:
            welcome_msg = self._t(
                "Welcome to KIC-AI Assistant - PCB Mode! 🔧🖥️\n\n"
                "I can help you with:\n"
                "• PCB layout analysis and advice\n"
                "• Component placement optimization\n"
                "• Routing suggestions\n"
                "• Design rule checking tips\n"
                "• Manufacturing considerations\n\n"
                "🔧 Interaction Modes:\n"
                "• Analysis: Safe recommendations only\n"
                "• Advisory: Step-by-step guidance\n"
                "• Assistant: Interactive help (future automation)\n\n"
                "💡 I remember our conversation!\n"
                "Ask me about your PCB design!",
                "欢迎使用 KIC-AI 助手 - PCB 模式！🔧🖥️\n\n"
                "我可以帮你：\n"
                "• PCB 布局分析与建议\n"
                "• 元器件摆放优化\n"
                "• 布线建议\n"
                "• 设计规则（DRC）检查提示\n"
                "• 制造可行性考虑\n\n"
                "🔧 交互模式：\n"
                "• 分析模式：仅安全建议\n"
                "• 顾问模式：分步指导\n"
                "• 助手模式：交互式帮助\n\n"
                "💡 我会记住我们的对话！\n"
                "有什么 PCB 设计问题尽管问我！")
        
        self.add_message("🤖 KIC-AI", welcome_msg)
        
    def apply_saved_settings(self):
        """Apply saved configuration settings"""
        try:
            # Load AI mode
            saved_mode = self.config_manager.get("ai_mode", "analysis")
            if saved_mode in ["analysis", "chat", "expert"]:
                self.interaction_mode = saved_mode
            
            # Language will be applied when the choice control is created
            
        except Exception as e:
            print(f"Error applying saved settings: {e}")
        
    def init_ui(self):
        """Initialiseer de user interface"""
        panel = wx.Panel(self)
        
        # Main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Mode selector
        mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        mode_label = wx.StaticText(panel, label=self._t("AI Interaction Mode:", "AI 交互模式："))
        mode_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        self.mode_choice = wx.Choice(panel, choices=[
            self._t("🔍 Analysis Mode (Safe)", "🔍 分析模式（安全）"),
            self._t("📋 Advisory Mode (Guided)", "📋 顾问模式（引导）"),
            self._t("🤖 Assistant Mode (Interactive)", "🤖 助手模式（交互）")
        ])
        # Apply saved mode
        saved_mode = self.config_manager.get("ai_mode", "analysis")
        mode_map = {"analysis": 0, "chat": 1, "expert": 2}
        self.mode_choice.SetSelection(mode_map.get(saved_mode, 0))
        
        mode_help = wx.Button(panel, label="?", size=(30, -1))
        mode_help.SetToolTip(self._t("Click for mode explanations", "点击查看模式说明"))
        
        mode_sizer.Add(mode_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        mode_sizer.Add(self.mode_choice, 1, wx.EXPAND | wx.RIGHT, 5)
        mode_sizer.Add(mode_help, 0, wx.ALIGN_CENTER_VERTICAL)
        
        main_sizer.Add(mode_sizer, 0, wx.EXPAND | wx.ALL, 10)
        # Language selector
        lang_sizer = wx.BoxSizer(wx.HORIZONTAL)
        lang_label = wx.StaticText(panel, label=self._t("Language / Taal:", "语言："))
        lang_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        self.lang_choice = wx.Choice(panel, choices=[
            "🇨🇳 中文",
            "🇬🇧 English"
        ])
        # Apply saved language
        self.ui_lang_code = "zh" if self.config_manager.get("language", "中文") == "中文" else "en"
        self.ui_zh = self.ui_lang_code == "zh"
        saved_lang = self.config_manager.get("language", "中文")
        lang_map = {
            "中文": 0, "English": 1
        }
        self.lang_choice.SetSelection(lang_map.get(saved_lang, 0))
        
        lang_sizer.Add(lang_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        lang_sizer.Add(self.lang_choice, 1, wx.EXPAND)
        
        main_sizer.Add(lang_sizer, 0, wx.EXPAND | wx.ALL, 10)

        
        # Chat area
        self.chat_ctrl = wx.TextCtrl(
            panel, 
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP
        )
        self.chat_ctrl.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        # Input area
        input_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.input_ctrl = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.input_ctrl.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.input_ctrl.SetHint(self._t("Type your question here...", "在这里输入你的问题..."))
        
        # Buttons
        self.send_btn = wx.Button(panel, label=self._t("Send", "发送"))
        analyze_label = self._t("Analyze Schematic", "分析原理图") if self.context_type == "schematic" else self._t("Analyze PCB", "分析 PCB")
        self.analyze_btn = wx.Button(panel, label=analyze_label)
        self.pricing_btn = wx.Button(panel, label=self._t("💰 Pricing", "💰 元件价格"))
        self.config_btn = wx.Button(panel, label=self._t("⚙️ Config", "⚙️ 设置"))
        self.clear_btn = wx.Button(panel, label=self._t("Clear Chat", "清空对话"))
        self.context_btn = wx.Button(panel, label=self._t("Show Context", "显示上下文"))
        self.web_search_btn = wx.Button(panel, label=self._t("🌐 Web Search", "🌐 联网搜索"))
        
        # Input layout
        input_sizer.Add(self.input_ctrl, 1, wx.EXPAND | wx.RIGHT, 5)
        input_sizer.Add(self.send_btn, 0, wx.RIGHT, 5)
        input_sizer.Add(self.analyze_btn, 0, wx.RIGHT, 5)
        input_sizer.Add(self.pricing_btn, 0, wx.RIGHT, 5)
        input_sizer.Add(self.config_btn, 0, wx.RIGHT, 5)
        input_sizer.Add(self.clear_btn, 0, wx.RIGHT, 5)
        input_sizer.Add(self.context_btn, 0, wx.RIGHT, 5)
        input_sizer.Add(self.web_search_btn, 0)
        
        # Status bar
        self.status_text = wx.StaticText(panel, label=self._t("Ready", "就绪"))
        self.status_text.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        
        # Main layout
        main_sizer.Add(self.chat_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(input_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        main_sizer.Add(self.status_text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        panel.SetSizer(main_sizer)
        
        # Events
        self.bind_events()
        
    def bind_events(self):
        """Bind UI events"""
        self.send_btn.Bind(wx.EVT_BUTTON, self.on_send)
        self.analyze_btn.Bind(wx.EVT_BUTTON, self.on_analyze)
        self.pricing_btn.Bind(wx.EVT_BUTTON, self.on_pricing)
        self.config_btn.Bind(wx.EVT_BUTTON, self.on_config)
        self.clear_btn.Bind(wx.EVT_BUTTON, self.on_clear)
        self.context_btn.Bind(wx.EVT_BUTTON, self.on_show_context)
        self.web_search_btn.Bind(wx.EVT_BUTTON, self.on_web_search)
        self.mode_choice.Bind(wx.EVT_CHOICE, self.on_mode_change)
        self.lang_choice.Bind(wx.EVT_CHOICE, self.on_lang_change)
        self.input_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_send)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        # Mode help button (find it in the parent)
        for child in self.GetChildren():
            for subchild in child.GetChildren():
                if isinstance(subchild, wx.Button) and subchild.GetLabel() == "?":
                    subchild.Bind(wx.EVT_BUTTON, self.on_mode_help)
                    break
        
    def _t(self, en, zh):
        """界面文本：中文为主，英文原样保留可对照"""
        return zh if getattr(self, "ui_zh", False) else en

    def add_message(self, sender, message):
        """Add message to chat"""
        timestamp = wx.DateTime.Now().Format("%H:%M")
        formatted_msg = f"[{timestamp}] {sender}:\n{message}\n\n"
        self.chat_ctrl.AppendText(formatted_msg)
        
    def set_status(self, status):
        """Update status tekst"""
        self.status_text.SetLabel(status)
        
    def on_send(self, event):
        """Send user message"""
        message = self.input_ctrl.GetValue().strip()
        if not message:
            return
            
        # Add message
        self.add_message(self._t("🟢 You", "🟢 我"), message)
        self.input_ctrl.Clear()
        
        # Send to AI
        self.process_user_message(message)
        
    def on_analyze(self, event):
        """Analyze current PCB"""
        self.set_status(self._t("Analyzing...", "分析中..."))
        self.analyze_btn.Enable(False)
        
        # Start analyse in thread
        thread = threading.Thread(target=self.analyze_pcb)
        thread.daemon = True
        thread.start()
        
    def on_clear(self, event):
        """Clear chat history"""
        self.chat_ctrl.Clear()
        self.conversation_history.clear()  # Wis ook conversatie geschiedenis
        self.add_message("🤖 KIC-AI", self._t("Chat cleared. How can I help you?", "对话已清空，有什么可以帮你？"))
        
    def on_mode_change(self, event):
        """Handle AI interaction mode change"""
        selection = self.mode_choice.GetSelection()
        
        if selection == 0:
            self.interaction_mode = self.ANALYSIS_MODE
            mode_name = "Analysis Mode"
            description = "Safe analysis and recommendations only"
        elif selection == 1:
            self.interaction_mode = self.ADVISORY_MODE
            mode_name = "Advisory Mode"
            description = "Step-by-step guidance with user confirmation"
        elif selection == 2:
            self.interaction_mode = self.ASSISTANT_MODE
            mode_name = "Assistant Mode"
            description = "Interactive recommendations and future automation"
        
        if self.ui_zh:
            mode_zh = {"Analysis Mode": "分析模式", "Advisory Mode": "顾问模式", "Assistant Mode": "助手模式"}
            desc_zh = {"Analysis Mode": "仅提供安全分析与建议", "Advisory Mode": "分步指导并在操作前确认", "Assistant Mode": "交互式建议与未来自动化"}
            self.add_message("⚙️ 系统", f"已切换到{mode_zh.get(mode_name, mode_name)}：{desc_zh.get(mode_name, description)}")
            self.set_status(f"模式：{mode_zh.get(mode_name, mode_name)}")
        else:
            self.add_message("⚙️ System", f"Switched to {mode_name}: {description}")
            self.set_status(f"Mode: {mode_name}")
        
    def on_mode_help(self, event):
        """Show mode explanations"""
        help_text = self._t(
"""🔍 Analysis Mode (Safe):
• Analyzes your design and provides recommendations
• No modifications to your project
• Safe for all users and projects

📋 Advisory Mode (Guided):
• Provides step-by-step instructions
• Asks for confirmation before suggesting changes
• Guides you through design improvements

🤖 Assistant Mode (Interactive):
• Interactive design recommendations
• Future: Semi-automatic design assistance
• Advanced features for experienced users

Choose the mode that fits your experience level and comfort with AI assistance.""",
"""🔍 分析模式（安全）：
• 分析你的设计并提供建议
• 不修改你的项目
• 适合所有用户和项目

📋 顾问模式（引导）：
• 提供分步操作指导
• 在建议修改前征求你的确认
• 引导你完成设计改进

🤖 助手模式（交互）：
• 交互式设计建议
• 未来：半自动设计辅助
• 面向经验丰富用户的高级功能

选择适合你经验水平和 AI 使用舒适度的模式。""")
        
        self.add_message(self._t("ℹ️ Mode Help", "ℹ️ 模式帮助"), help_text)
        
    def on_show_context(self, event):
        """Toon huidige conversatie context"""
        if not self.conversation_history:
            self.add_message("ℹ️ Context", self._t("No conversation history yet.", "还没有对话历史。"))
            return
            
        context_info = f"📝 Memory: {len(self.conversation_history)//2} exchanges remembered\n\n"
        
        # Show last 4 messages (2 exchanges)
        recent_history = self.conversation_history[-4:] if len(self.conversation_history) > 4 else self.conversation_history
        
        for entry in recent_history:
            role_emoji = "🟢" if entry['role'] == "User" else "🤖"
            content = entry['content'][:150] + "..." if len(entry['content']) > 150 else entry['content']
            context_info += f"{role_emoji} {content}\n\n"
            
        if len(self.conversation_history) > 4:
            context_info += f"(+ {len(self.conversation_history)//2 - 2} older exchanges in memory)"
            
        self.add_message(self._t("ℹ️ Context", "ℹ️ 上下文"), context_info)
        
    def on_lang_change(self, event):
        """语言切换即时生效并保存"""
        selection = self.lang_choice.GetSelection()
        lang_names = {0: "中文", 1: "English"}
        if selection in lang_names:
            self.config_manager.set("language", lang_names[selection])
            self.config_manager.save_config()
        self.ui_lang_code = "zh" if self.config_manager.get("language", "中文") == "中文" else "en"
        self.ui_zh = self.ui_lang_code == "zh"
        self.set_status(self._t("Language: " + lang_names.get(selection, ""), "语言：" + lang_names.get(selection, "")))

    def on_close(self, event):
        """Sluit dialog"""
        self.Destroy()
        
    def analyze_pcb(self):
        """Analyze current design in background thread"""
        try:
            if self.context_type == "schematic":
                # Analyze schematic
                analysis = self.collect_schematic_info()
                analysis_title = "📋 Schematic Analysis"
                ai_prompt = f"Analyze this schematic design and provide circuit advice:\n\n{analysis}"
            else:
                # Analyze PCB
                board = pcbnew.GetBoard()
                if not board:
                    wx.CallAfter(self.add_message, "❌ Error", "No PCB loaded")
                    return
                    
                analysis = self.collect_pcb_info(board)
                analysis_title = "📊 PCB Analysis"
                ai_prompt = f"Analyze this PCB and provide design advice:\n\n{analysis}"
            
            # Toon analyse
            wx.CallAfter(self.add_message, analysis_title, analysis)
            
            # Stuur naar AI voor advies
            self.send_to_ai(ai_prompt, is_analysis=True)
            
        except Exception as e:
            wx.CallAfter(self.add_message, "❌ Error", f"Analysis error: {str(e)}")
        finally:
            wx.CallAfter(self.analyze_btn.Enable, True)
            wx.CallAfter(self.set_status, "Ready")
            
    def collect_pcb_info(self, board):
        """Collect PCB information with specific component details"""
        info = []
        
        # Board info
        title = board.GetTitleBlock().GetTitle()
        info.append(f"PCB: {title if title else 'Unknown'}")
        
        # Afmetingen
        bbox = board.GetBoardEdgesBoundingBox()
        width_mm = bbox.GetWidth() / 1000000.0
        height_mm = bbox.GetHeight() / 1000000.0
        info.append(f"Dimensions: {width_mm:.1f} x {height_mm:.1f} mm")
        
        # Componenten - GEDETAILLEERDE LIJST
        footprints = list(board.GetFootprints())
        info.append(f"Components: {len(footprints)}")
        
        if footprints:
            info.append("\n=== COMPONENT DETAILS ===")
            
            # Sorteer componenten op referentie
            sorted_footprints = sorted(footprints, key=lambda fp: fp.GetReference())
            
            for fp in sorted_footprints:
                ref = fp.GetReference()
                value = fp.GetValue()
                footprint = fp.GetFPID().GetLibItemName()
                
                # Positie
                pos = fp.GetPosition()
                x_mm = pos.x / 1000000.0
                y_mm = pos.y / 1000000.0
                
                # Rotatie
                rotation = fp.GetOrientation().AsDegrees()
                
                # Layer (bovenkant/onderkant)
                layer = "Top" if fp.IsFlipped() == False else "Bottom"
                
                info.append(f"{ref}: {value}")
                info.append(f"  Footprint: {footprint}")
                info.append(f"  Position: ({x_mm:.1f}, {y_mm:.1f}) mm")
                info.append(f"  Rotation: {rotation:.0f}°, Layer: {layer}")
                
                # Pads info
                pads = list(fp.Pads())
                if pads:
                    info.append(f"  Pads: {len(pads)}")
                
                info.append("")  # Lege regel tussen componenten
        
        # Nets met details
        nets = board.GetNetInfo()
        net_count = nets.GetNetCount()
        info.append(f"\n=== NETS ({net_count}) ===")
        
        # Toon belangrijke nets
        for net_code in range(min(10, net_count)):  # Eerste 10 nets
            net = nets.GetNetItem(net_code)
            if net:
                net_name = net.GetNetname()
                if net_name and net_name != "":
                    info.append(f"Net {net_code}: {net_name}")
        
        # Tracks
        tracks = list(board.GetTracks())
        info.append(f"\nTracks: {len(tracks)}")
        
        # Layers
        layer_count = board.GetCopperLayerCount()
        info.append(f"Copper layers: {layer_count}")
        
        return "\n".join(info)
    
    def collect_schematic_info(self):
        """Collect schematic information for analysis"""
        info = []
        
        try:
            # Try to get schematic information via PCB board 
            # (KiCad stores schematic refs in PCB)
            board = pcbnew.GetBoard()
            if not board:
                info.append("No board available for schematic analysis")
                return "\n".join(info)
            
            # Board/Project info
            title = board.GetTitleBlock().GetTitle()
            info.append(f"Project: {title if title else 'Unknown'}")
            
            # Get footprints (which represent schematic symbols)
            footprints = list(board.GetFootprints())
            info.append(f"Components: {len(footprints)}")
            
            if footprints:
                info.append("\n=== SCHEMATIC COMPONENTS ===")
                
                # Group by component type
                components_by_type = {}
                
                for fp in footprints:
                    ref = fp.GetReference()
                    value = fp.GetValue()
                    footprint = fp.GetFPID().GetLibItemName()
                    
                    # Get component type from reference
                    comp_type = ref[0] if ref else "?"
                    
                    if comp_type not in components_by_type:
                        components_by_type[comp_type] = []
                    
                    components_by_type[comp_type].append({
                        'ref': ref,
                        'value': value,
                        'footprint': footprint
                    })
                
                # Show components grouped by type
                for comp_type in sorted(components_by_type.keys()):
                    components = components_by_type[comp_type]
                    info.append(f"\n{comp_type}-type components ({len(components)}):")
                    
                    for comp in sorted(components, key=lambda x: x['ref']):
                        info.append(f"  {comp['ref']}: {comp['value']} ({comp['footprint']})")
            
            # Nets (connections between components)
            nets = board.GetNetInfo()
            net_count = nets.GetNetCount()
            info.append(f"\n=== CONNECTIONS ({net_count} nets) ===")
            
            # Show important nets
            important_nets = []
            for net_code in range(min(15, net_count)):
                net = nets.GetNetItem(net_code)
                if net:
                    net_name = net.GetNetname()
                    if net_name and net_name != "":
                        important_nets.append(net_name)
            
            if important_nets:
                info.append("Key nets:")
                for net_name in important_nets:
                    info.append(f"  • {net_name}")
            
            info.append(f"\nTotal design complexity: {len(footprints)} components, {net_count} connections")
            
        except Exception as e:
            info.append(f"Schematic analysis error: {str(e)}")
            info.append("Note: Full schematic analysis requires KiCad eeschema integration")
        
        return "\n".join(info)
        
    def process_user_message(self, message):
        """Process user message"""
        self.set_status("AI thinking...")
        self.send_btn.Enable(False)
        
        # Check for component-specific guidance in Assistant mode
        specific_guidance = self.get_component_specific_guidance(message)
        if specific_guidance:
            self.add_message("🤖 Assistant", specific_guidance)
            self.send_btn.Enable(True)
            self.set_status("Ready")
            return
        # Start AI processing in thread
        thread = threading.Thread(target=self.send_to_ai, args=(message,))
        thread.daemon = True
        thread.start()
        
    def send_to_ai(self, message, is_analysis=False):
        """Send message to AI (Ollama) with design context"""
        if not REQUESTS_AVAILABLE:
            wx.CallAfter(self.add_message, "❌ Error", self._t("Requests module not available", "缺少 requests 模块"))
            wx.CallAfter(self.send_btn.Enable, True)
            wx.CallAfter(self.set_status, "Ready")
            return
            
        try:
            # ---- AI 后端配置（云端 OpenAI 兼容 API 或本地 Ollama） ----
            LLM_PROVIDERS = {
                "deepseek": ("https://api.deepseek.com", "deepseek-chat"),
                "openai":   ("https://api.openai.com/v1", "gpt-4o-mini"),
                "zhipu":    ("https://open.bigmodel.cn/api/paas/v4", "glm-4-flash"),
                "qwen":     ("https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus"),
                "minimax":  ("https://api.minimax.chat/v1", "MiniMax-Text-01"),
                "custom":   ("", ""),
            }
            llm_provider = self.config_manager.get("llm_provider", "deepseek")
            llm_api_key = self.config_manager.get("llm_api_key", "").strip()
            llm_api_base = self.config_manager.get("llm_api_base", "").strip()
            llm_model = self.config_manager.get("llm_model", "").strip()
            _default_base, _default_model = LLM_PROVIDERS.get(llm_provider, LLM_PROVIDERS["deepseek"])
            api_base = (llm_api_base or _default_base).rstrip("/")
            api_model = llm_model or _default_model
            use_cloud = bool(llm_api_key) and bool(api_base)

            # Build simple conversation context
            conversation_context = ""
            if self.conversation_history:
                # Include last 4 exchanges (8 messages) for context
                recent_messages = self.conversation_history[-8:]
                conversation_context = "\n\nRecent conversation:\n"
                for msg in recent_messages:
                    conversation_context += f"{msg['role']}: {msg['content'][:200]}...\n"
                conversation_context += "\n"
            
            # Get current design context for user questions
            design_context = ""
            if not is_analysis:
                try:
                    if self.context_type == "schematic":
                        design_context = f"\n\nCURRENT SCHEMATIC CONTEXT:\n{self.collect_schematic_info()}\n"
                    else:
                        board = pcbnew.GetBoard()
                        if board:
                            design_context = f"\n\nCURRENT PCB CONTEXT:\n{self.collect_pcb_info(board)}\n"
                except:
                    pass  # No design available
            
            # Prepare system prompt based on context and interaction mode
            mode_instructions = self.get_mode_instructions()
            language_instructions = self.get_language_prompt()
            
            # Debug: Print language instructions to verify they're working
            if language_instructions:
                print(f"DEBUG: Language instructions: {language_instructions}")
            
            if is_analysis:
                if self.context_type == "schematic":
                    system_prompt = (f"{language_instructions} "
                                   "You are an expert electronic circuit designer and schematic review specialist. "
                                   "Analyze the provided schematic data thoroughly and provide specific, practical advice. "
                                   "Look at component types, values, connections, and circuit topology. "
                                   "Focus on circuit functionality, component selection, and design best practices. "
                                   f"{mode_instructions} "
                                   "Reference previous conversation if relevant.")
                else:
                    system_prompt = (f"{language_instructions} "
                                   "You are an expert PCB design engineer. Analyze the provided PCB data thoroughly and provide specific, practical advice. "
                                   "Look at individual components, their values, positions, and relationships. "
                                   f"{mode_instructions} "
                                   "Reference previous conversation if relevant.")
            else:
                if self.context_type == "schematic":
                    system_prompt = (f"{language_instructions} "
                                   "You are a helpful schematic design assistant with access to the current schematic design. "
                                   "When users ask about specific components, circuits, or connections, reference the actual schematic data provided. "
                                   "Give specific answers about component values, connections, and circuit topology when possible. "
                                   "Focus on circuit functionality, component selection, and electrical design principles. "
                                   f"{mode_instructions} "
                                   "Remember our conversation and build upon previous topics when relevant.")
                else:
                    system_prompt = (f"{language_instructions} "
                                   "You are a helpful PCB design assistant with access to the current PCB design. "
                                   "When users ask about specific components (like resistors, capacitors, ICs), look up the actual component details from the PCB context provided. "
                                   "Give specific answers referencing actual component values, positions, and designators when possible. "
                                   "If asked about a specific component (e.g., 'R1', 'check this resistor'), find that component in the PCB data and provide detailed information about it. "
                                   f"{mode_instructions} "
                                   "Remember our conversation and build upon previous topics when relevant.")
            
            # Build final prompt with design context
            # Add language instruction again at the end for extra emphasis
            language_reminder = ""
            if language_instructions:
                language_reminder = f"\n\nREMEMBER: {language_instructions}"
            
            final_prompt = system_prompt + conversation_context + design_context + f"\nUser question: {message}\n\nPlease provide a specific, helpful response based on the actual design data when applicable:{language_reminder}"
            
            # API request
            if use_cloud:
                # ---- 云端 OpenAI 兼容模式（DeepSeek/OpenAI/智谱/通义/MiniMax/自定义） ----
                url = api_base + "/chat/completions"
                headers = {
                    "Authorization": "Bearer " + llm_api_key,
                    "Content-Type": "application/json",
                }
                messages = [{"role": "system", "content": system_prompt}]
                for h in self.conversation_history[-8:]:
                    role = "assistant" if h.get("role") == "Assistant" else "user"
                    messages.append({"role": role, "content": str(h.get("content", ""))[:1000]})
                # 联网搜索：关键词触发，把实时搜索结果注入上下文
                web_ctx = ""
                if self.config_manager.get("websearch_enabled", True) and \
                        any(k in message for k in ["搜索", "查一下", "查一查", "最新", "今天", "现在", "新闻", "价格", "上市", "发布", "2026"]):
                    _results = self.web_search(message)
                    if _results:
                        web_ctx, _disp = self.format_web_results(_results)
                        wx.CallAfter(self.add_message, "🌐 联网搜索", _disp)
                messages.append({
                    "role": "user",
                    "content": (web_ctx + "\n\n" if web_ctx else "") + design_context + f"\nUser question: {message}\n\nPlease provide a specific, helpful response based on the actual design data when applicable:{language_reminder}",
                })
                data = {"model": api_model, "messages": messages, "stream": False, "temperature": 0.3}
                response = requests.post(url, headers=headers, json=data, timeout=120)
                if response.status_code == 200:
                    result = response.json()
                    try:
                        ai_response = result["choices"][0]["message"]["content"].strip()
                    except (KeyError, IndexError, TypeError):
                        ai_response = "No response received"
                else:
                    detail = response.text[:200].replace("\n", " ")
                    wx.CallAfter(self.add_message, "❌ Error",
                                 f"{self._t('AI API error', 'AI API 错误')}: {response.status_code} {detail}")
                    ai_response = None
            else:
                # ---- 本地 Ollama 模式（未配置云端 API Key 时的回退） ----
                url = "http://localhost:11434/api/generate"
                data = {
                    "model": "llama3.2:3b",
                    "prompt": final_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.8,
                        "num_ctx": 4096,
                        "repeat_penalty": 1.2,
                        "top_k": 20
                    }
                }
                response = requests.post(url, json=data, timeout=60)
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result.get('response', 'No response received').strip()
                else:
                    wx.CallAfter(self.add_message, "❌ Error", f"{self._t('AI server error', 'AI 服务器错误')}: {response.status_code}")
                    ai_response = None
            
            if ai_response:
                # Add to conversation history
                self.conversation_history.append({"role": "User", "content": message})
                self.conversation_history.append({"role": "Assistant", "content": ai_response})
                
                # Keep only last 12 messages (6 exchanges)
                if len(self.conversation_history) > 12:
                    self.conversation_history = self.conversation_history[-12:]
                
                wx.CallAfter(self.add_message, "🤖 KIC-AI", ai_response)
                
        except requests.exceptions.ConnectionError:
            wx.CallAfter(self.add_message, "❌ Error", 
                        self._t(
                            "Cannot connect to the AI server.\nCloud API: check network and API key in settings.\nLocal Ollama: start it with 'ollama serve'",
                            "无法连接 AI 服务器。\n云端 API：请检查网络和设置中的 API 密钥。\n本地 Ollama：请运行 'ollama serve'"))
        except requests.exceptions.Timeout:
            wx.CallAfter(self.add_message, "❌ Error", self._t("AI timeout - please try again", "AI 超时，请重试"))
        except Exception as e:
            wx.CallAfter(self.add_message, "❌ Error", f"{self._t('AI error', 'AI 错误')}: {str(e)}")
        finally:
            wx.CallAfter(self.send_btn.Enable, True)
            wx.CallAfter(self.set_status, "Ready")
    
    def web_search(self, query):
        """DeepSeek 原生联网搜索（Anthropic 兼容接口 + web_search_20250305 工具）"""
        if not REQUESTS_AVAILABLE:
            return None
        key = self.config_manager.get("llm_api_key", "").strip()
        if not key:
            return None
        model = self.config_manager.get("websearch_model", "deepseek-v4-flash") or "deepseek-v4-flash"
        try:
            max_uses = max(1, min(5, int(self.config_manager.get("websearch_max_uses", 3) or 3)))
        except Exception:
            max_uses = 3
        url = "https://api.deepseek.com/anthropic/v1/messages"
        headers = {
            "x-api-key": key,
            "authorization": "Bearer " + key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "accept": "application/json",
            "user-agent": "kic-ai-plugin/1.0",
        }
        body = {
            "model": model,
            "max_tokens": 1024,
            "messages": [{
                "role": "user",
                "content": [{"type": "text", "text": "Perform a web search for the query: " + query}],
            }],
            "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": max_uses}],
        }
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=60)
        except Exception:
            return None
        if resp.status_code != 200:
            return None
        try:
            return self._parse_web_results(resp.json())
        except Exception:
            return None

    def _parse_web_results(self, data):
        """解析 DeepSeek 搜索响应：结果列表 + 引文摘要"""
        results = []
        snippets = {}
        blocks = data.get("content", []) or []
        for b in blocks:
            if b.get("type") == "text":
                for c in (b.get("citations") or []):
                    u = c.get("url") or ""
                    t = c.get("cited_text") or ""
                    if u and t and u not in snippets:
                        snippets[u] = t
        for b in blocks:
            if b.get("type") == "web_search_tool_result":
                for item in (b.get("content") or []):
                    if item.get("type") != "web_search_result":
                        continue
                    u = item.get("url") or ""
                    if not u:
                        continue
                    results.append({
                        "url": u,
                        "title": item.get("title") or "",
                        "snippet": snippets.get(u, ""),
                        "date": item.get("page_age") or "",
                    })
        return results

    def format_web_results(self, results):
        """把搜索结果格式化成给大模型的上下文 + 展示文本"""
        if not results:
            return None, None
        ctx_lines = ["以下是从互联网实时搜索到的资料（来源：DeepSeek 原生搜索）："]
        disp_lines = []
        for i, r in enumerate(results[:8], 1):
            title = r["title"] or r["url"]
            ctx_lines.append(f"{i}. {title}\n   来源: {r['url']}")
            if r["snippet"]:
                ctx_lines.append(f"   摘要: {r['snippet'][:400]}")
            if r["date"]:
                ctx_lines.append(f"   时间: {r['date']}")
            disp_lines.append(f"{i}. {title}  {r['url']}")
            if r["snippet"]:
                disp_lines.append(f"   {r['snippet'][:150]}")
        return "\n".join(ctx_lines), "\n".join(disp_lines)

    def on_web_search(self, event):
        """🌐 手动联网搜索按钮"""
        dlg = wx.TextEntryDialog(self, self._t("Enter a search query:", "输入要搜索的内容："),
                                 self._t("Web Search", "联网搜索"), "")
        if dlg.ShowModal() != wx.ID_OK or not dlg.GetValue().strip():
            dlg.Destroy()
            return
        query = dlg.GetValue().strip()
        dlg.Destroy()
        self.set_status(self._t("Searching the web...", "正在联网搜索..."))
        self.web_search_btn.Enable(False)
        thread = threading.Thread(target=self._run_web_search, args=(query,))
        thread.daemon = True
        thread.start()

    def _run_web_search(self, query):
        """后台执行联网搜索并展示结果"""
        try:
            results = self.web_search(query)
            if results:
                _, disp = self.format_web_results(results)
                wx.CallAfter(self.add_message, "🌐 联网搜索", disp)
                self.conversation_history.append({"role": "User", "content": "[联网搜索] " + query})
                self.conversation_history.append({"role": "Assistant", "content": "（已展示联网搜索结果，见上方来源列表）"})
            else:
                wx.CallAfter(self.add_message, "❌ Error",
                             self._t("Web search failed. Check your DeepSeek API key or network.",
                                     "联网搜索失败：请检查 DeepSeek API 密钥或网络。"))
        finally:
            wx.CallAfter(self.web_search_btn.Enable, True)
            wx.CallAfter(self.set_status, self._t("Ready", "就绪"))

    def get_mode_instructions(self):
        """Get instructions based on current interaction mode"""
        if self.interaction_mode == self.ANALYSIS_MODE:
            return ("ANALYSIS MODE: Provide only analysis and recommendations. "
                   "Do not suggest any direct modifications to the design. "
                   "Focus on observations and general advice.")
        
        elif self.interaction_mode == self.ADVISORY_MODE:
            return ("ADVISORY MODE: Provide step-by-step instructions when suggesting changes. "
                   "Always ask for user confirmation before proceeding with multi-step processes. "
                   "Format suggestions as clear actionable steps with safety warnings when needed. "
                   "Example: 'To remove R14: 1) First select the component 2) Press Delete 3) Update the netlist. Would you like me to guide you through this?'")
        
        elif self.interaction_mode == self.ASSISTANT_MODE:
            return ("ASSISTANT MODE: Provide interactive design assistance. "
                   "You can suggest specific actions and modifications. "
                   "When appropriate, indicate what changes could be made automatically in the future. "
                   "Be proactive in offering to help with implementation.")
        
        return ""
    
    def process_user_message(self, message):
        """Process user message with mode-specific handling"""
        self.send_btn.Enable(False)
        self.set_status("Processing...")
        
        # Check for mode-specific commands
        if self.interaction_mode == self.ADVISORY_MODE:
            if any(word in message.lower() for word in ['remove', 'delete', 'change', 'modify', 'update']):
                # Add advisory warning
                self.add_message("⚠️ Advisory", 
                               "I'll provide step-by-step guidance for this modification. "
                               "Please confirm each step before proceeding.")
        
        elif self.interaction_mode == self.ASSISTANT_MODE:
            if any(word in message.lower() for word in ['remove', 'delete', 'change', 'modify']):
                # Add assistant note
                self.add_message("🤖 Assistant", 
                               "I'll provide interactive guidance. In future versions, "
                               "I may be able to help automate some of these tasks.")
        
        # Check for component-specific guidance in Assistant mode
        specific_guidance = self.get_component_specific_guidance(message)
        if specific_guidance:
            self.add_message("🤖 Assistant", specific_guidance)
            self.send_btn.Enable(True)
            self.set_status("Ready")
            return
        # Start AI processing in thread
        thread = threading.Thread(target=self.send_to_ai, args=(message,))
        thread.daemon = True
        thread.start()
    
    def get_component_specific_guidance(self, message):
        """Provide specific guidance for common component operations"""
        if self.interaction_mode != self.ASSISTANT_MODE:
            return None
            
        message_lower = message.lower()
        
        # Check for specific component removal requests
        if any(phrase in message_lower for phrase in ['remove j', 'delete j', 'remove connector']):
            component = None
            # Extract component reference
            import re
            match = re.search(r'[jJ]\d+', message)
            if match:
                component = match.group(0).upper()
            
            if component:
                return f"""🔧 **Removing {component} - Step-by-step:**

1. **Select the component:**
   - Click on {component} in the PCB layout
   - The component should highlight in selection color

2. **Delete the component:**
   - Press **Delete** key, or
   - Right-click → Delete, or  
   - Use Edit → Delete from menu

3. **Clean up connections:**
   - Check for any remaining tracks/vias
   - Delete orphaned connections if needed

4. **Update schematic (if needed):**
   - Switch to schematic editor
   - Remove {component} from schematic too
   - Run Tools → Update PCB from Schematic

5. **Verify design:**
   - Check Design Rules (DRC)
   - Verify no missing connections

Would you like me to explain any of these steps in more detail?"""
        
        return None
    def get_language_prompt(self):
        """Get language-specific prompt addition"""
        selection = self.lang_choice.GetSelection()
        if selection == -1:
            selection = 0  # Default to English
            
        lang_info = self.LANGUAGES[selection]
        lang_code = lang_info["code"]
        
        if lang_code == "en":
            return ""  # English is default
        elif lang_code == "nl":
            return "U MOET antwoorden in het Nederlands! Alle antwoorden in het Nederlands. Nederlandse termen voor elektronica gebruiken. Niet in het Engels antwoorden."
        elif lang_code == "de":
            return "Antworten Sie auf Deutsch! Alle Antworten auf Deutsch schreiben. Deutsche Begriffe fuer Elektronik verwenden. Nicht auf Englisch antworten."
        elif lang_code == "es":
            return "Responder en espanol! Todas las respuestas en espanol. Usar terminos tecnicos en espanol. No responder en ingles."
        elif lang_code == "fr":
            return "Repondre en francais! Toutes les reponses en francais. Utiliser des termes techniques francais. Ne pas repondre en anglais."
        elif lang_code == "zh":
            return "请务必用中文回答！所有回答都用中文。使用中文电子专业术语。不要用英文回答。"
        elif lang_code == "en":
            return ""
        else:
            return ""

    def on_pricing(self, event):
        """Get component pricing via Nexar API"""
        self.set_status(self._t("Getting pricing...", "正在获取价格..."))
        self.pricing_btn.Enable(False)
        
        # Start pricing in thread
        thread = threading.Thread(target=self.get_component_pricing)
        thread.daemon = True
        thread.start()
        
    def get_component_pricing(self):
        """Get pricing for components in current design"""
        try:
            # Import the MCP client
            import sys
            import os
            
            # Add the plugins directory to path so we can import simple_mcp_client
            plugins_dir = os.path.dirname(os.path.abspath(__file__))
            if plugins_dir not in sys.path:
                sys.path.insert(0, plugins_dir)
                
            from simple_mcp_client_embedded import SimpleMCPClient
            
            # Get components from current design
            board = pcbnew.GetBoard()
            if not board:
                wx.CallAfter(self.add_message, "❌ Error", "No PCB loaded")
                return
                
            footprints = list(board.GetFootprints())
            if not footprints:
                wx.CallAfter(self.add_message, "💰 Pricing", "No components found in PCB")
                return
            
            # Get API key from configuration
            nexar_api_key = self.config_manager.get_nexar_api_key()
            
            # Create MCP client with API key
            client = SimpleMCPClient(api_key=nexar_api_key)
            
            # Start Nexar server (should work in demo mode without API key)
            wx.CallAfter(self.add_message, "💰 Pricing", "🚀 Starting Nexar pricing service...")
            
            if not client.start_nexar_server():
                # Get more detailed error info
                error_msg = "Failed to start Nexar pricing server.\n\n"
                error_msg += "💡 This should work in demo mode without API keys.\n"
                error_msg += "Please check that Python3 is installed and working.\n\n"
                error_msg += "Debug info:\n"
                error_msg += f"• Python executable: python3\n"
                error_msg += f"• Server path: mcp_servers/nexar.py\n"
                error_msg += f"• Working directory: {os.getcwd()}\n"
                
                wx.CallAfter(self.add_message, "❌ Error", error_msg)
                return
            
            wx.CallAfter(self.add_message, "💰 Pricing", "🔍 Searching for component pricing...")
            
            # Get unique component values for pricing
            component_values = set()
            component_refs = {}  # Track which refs use which values
            
            for fp in footprints:
                value = fp.GetValue().strip()
                ref = fp.GetReference()
                
                if value and value not in ['', '~', 'DNP']:
                    component_values.add(value)
                    if value not in component_refs:
                        component_refs[value] = []
                    component_refs[value].append(ref)
            
            if not component_values:
                wx.CallAfter(self.add_message, "💰 Pricing", "No component values found for pricing")
                return
            
            # Search for pricing on unique values
            pricing_results = []
            found_count = 0
            
            for value in sorted(component_values):
                try:
                    results = client.search_parts(value)
                    
                    if results and len(results) > 0:
                        best_match = results[0]  # Take first result
                        refs_using = component_refs[value]
                        
                        pricing_results.append({
                            'value': value,
                            'refs': refs_using,
                            'part': best_match
                        })
                        found_count += 1
                        
                        # Progress update
                        wx.CallAfter(self.add_message, "💰 Progress", 
                                   f"✅ Found pricing for {value} (used by: {', '.join(refs_using[:3])}{'...' if len(refs_using) > 3 else ''})")
                        
                except Exception as e:
                    print(f"Error searching for {value}: {e}")
                    continue
            
            # Stop the server
            client.stop_server()
            
            # Format results
            if not pricing_results:
                wx.CallAfter(self.add_message, "💰 Pricing", 
                           "No pricing found. This is normal for custom values like resistor/capacitor values.\n"
                           "Try searching for specific part numbers instead.")
                return
            
            # Create pricing report
            report = f"💰 **COMPONENT PRICING REPORT**\n\n"
            report += f"Found pricing for {found_count}/{len(component_values)} unique component values:\n\n"
            
            total_cost = 0.0
            
            for result in pricing_results:
                value = result['value']
                refs = result['refs']
                part = result['part']
                
                report += f"**{value}** (x{len(refs)})\n"
                report += f"Used by: {', '.join(refs[:5])}{'...' if len(refs) > 5 else ''}\n"
                
                if 'part_number' in part:
                    report += f"Part: {part['part_number']}\n"
                if 'manufacturer' in part:
                    report += f"Mfg: {part['manufacturer']}\n"
                
                # Show pricing from different distributors
                if 'pricing' in part and part['pricing']:
                    report += "Pricing (qty 1):\n"
                    for distributor, price_info in part['pricing'].items():
                        price = price_info.get('price_1', 'N/A')
                        stock = price_info.get('stock', 'N/A')
                        report += f"  • {distributor}: ${price} (stock: {stock})\n"
                        
                        # Add to total cost estimate (using first available price)
                        if isinstance(price, (int, float)) and price > 0:
                            total_cost += price * len(refs)
                
                report += "\n"
            
            if total_cost > 0:
                report += f"**Estimated total cost: ${total_cost:.2f}**\n"
                report += "(Based on quantity 1 pricing - bulk pricing may be available)\n\n"
            
            report += "💡 **Tips:**\n"
            report += "• Prices are from demo data - real API provides live pricing\n"
            report += "• Bulk quantities often have better pricing\n"
            report += "• Consider component availability and lead times\n"
            report += "• Some generic values (like 10kΩ) may not have specific parts matched"
            
            wx.CallAfter(self.add_message, "💰 Pricing Report", report)
            
        except ImportError as e:
            wx.CallAfter(self.add_message, "❌ Error", 
                        f"MCP client not available: {e}\n"
                        "The simple_mcp_client.py file may be missing.")
        except Exception as e:
            wx.CallAfter(self.add_message, "❌ Error", f"Pricing error: {str(e)}")
        finally:
            wx.CallAfter(self.pricing_btn.Enable, True)
            wx.CallAfter(self.set_status, "Ready")

    def on_config(self, event):
        """Open configuration dialog"""
        try:
            # Create and show configuration dialog
            config_dialog = ConfigDialog(self, self.config_manager)
            
            if config_dialog.ShowModal() == wx.ID_OK:
                # Configuration was saved, apply new settings
                self.apply_saved_settings()
                
                # Update UI elements to reflect new settings
                self.update_ui_from_config()
                
                # Show confirmation
                self.add_message("⚙️ Config", self._t("Configuration updated successfully!", "配置更新成功！"))
            
            config_dialog.Destroy()
            
        except Exception as e:
            wx.MessageBox(f"{self._t('Config error', '配置错误')}: {str(e)}", self._t("Error", "错误"), wx.OK | wx.ICON_ERROR)
    
    def update_ui_from_config(self):
        """Update UI elements from configuration"""
        try:
            # Update mode selection
            saved_mode = self.config_manager.get("ai_mode", "analysis")
            mode_map = {"analysis": 0, "chat": 1, "expert": 2}
            mode_selection = mode_map.get(saved_mode, 0)
            self.mode_choice.SetSelection(mode_selection)
            self.interaction_mode = saved_mode
            
            # Update language selection
            saved_lang = self.config_manager.get("language", "中文")
            lang_map = {
                "中文": 0, "English": 1
            }
            lang_selection = lang_map.get(saved_lang, 0)
            self.lang_choice.SetSelection(lang_selection)
            
        except Exception as e:
            print(f"Error updating UI from config: {e}")

