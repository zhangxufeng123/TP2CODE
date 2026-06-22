# filepath: src/gui/main_window.py
import os
import sys
import re
import json
import pandas as pd

# ========================================================
# 🛠️ 路径注入
# ========================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem, 
                             QComboBox, QLineEdit, QFormLayout, QPushButton, QHeaderView,
                             QMessageBox, QFileDialog, QLabel, QGroupBox, QDialog)

from gui.custom_widgets import CheckableComboBox
from parsers.tp_parser import TestPlanParser
from core.smart_mapper import SmartPinMapper

def get_available_active_circuits():
    return [
        "ChargeRelease", 
        "BUF634A_SOP8", 
        "OPA145_INA141", 
        "OPA189", 
        "SN74LVC2G17DBVR",
        "TPS78401DRVR_3.3V"
    ]

# ========================================================
# 多态参数配置器
# ========================================================
class ParamEditorDialog(QDialog):
    def __init__(self, current_json, configurable_modules, parent=None):
        super().__init__(parent)
        self.setWindowTitle("模块独立参数配置 (按模块划分)")
        self.resize(450, 250) 
        self.layout = QVBoxLayout(self)
        
        try:
            data = json.loads(current_json) if current_json else {}
        except:
            data = {}
            
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        self.editors = {}
        
        ATE_RESOURCES = ["FPVIe", "FXVIe", "ACM200", "DCM", "HPSM"]
        
        for circuit in configurable_modules:
            tab = QWidget()
            form = QFormLayout(tab)
            circuit_data = data.get(circuit, {})
            if not isinstance(circuit_data, dict): circuit_data = {}
            
            current_editors = {}

            if "TPS78401" in circuit:
                out_net_edit = QLineEdit(circuit_data.get("OUTPUT_NET", ""))
                out_net_edit.setPlaceholderText("例如: +3.3V_ANA (生成此网络供其他模块调用)")
                form.addRow("输出电源网络 (Output Net):", out_net_edit)
                
                group_edit = QLineEdit(circuit_data.get("GROUP_ID", ""))
                group_edit.setPlaceholderText("例如: LDO_1")
                form.addRow("实例化组号 (Group):", group_edit)
                
                current_editors["OUTPUT_NET"] = out_net_edit
                current_editors["GROUP_ID"] = group_edit

            elif circuit == "OPA145_INA141":
                role_cb = QComboBox()
                role_cb.addItems(["IN+ (正端)", "IN- (负端)"])
                saved_role = circuit_data.get("ROLE", "IN+ (正端)")
                index = role_cb.findText(saved_role)
                if index >= 0: role_cb.setCurrentIndex(index)
                
                group_edit = QLineEdit(circuit_data.get("GROUP_ID", ""))
                group_edit.setPlaceholderText("例如: AMP_1 (必填，用于MUX分组)")
                
                vcc_edit = QLineEdit(circuit_data.get("VCC_NET", ""))
                vcc_edit.setPlaceholderText("例如: +3.3V_ANA (填入LDO配置的输出网络)")
                
                form.addRow("接入端角色 (Role):", role_cb)
                form.addRow("共享模块组号 (Group):", group_edit)
                form.addRow("模块正电源 (VCC Net):", vcc_edit)
                
                current_editors["ROLE_CB"] = role_cb
                current_editors["GROUP_ID"] = group_edit
                current_editors["VCC_NET"] = vcc_edit

            elif circuit == "QTMUe":
                path_cb = QComboBox()
                path_cb.addItems(["A (路径A)", "B (路径B)"])
                saved_path = circuit_data.get("QTMU_PATH", "A (路径A)")
                index = path_cb.findText(saved_path)
                if index >= 0: path_cb.setCurrentIndex(index)
                
                group_edit = QLineEdit(circuit_data.get("GROUP_ID", ""))
                group_edit.setPlaceholderText("例如: QTMU_Pair_1 (同组引脚将复用同一母线)")
                
                form.addRow("配对组号 (Group):", group_edit)
                form.addRow("QTMU 测量路径 (Path):", path_cb)
                
                current_editors["GROUP_ID"] = group_edit
                current_editors["QTMU_PATH"] = path_cb
                
            elif circuit in ATE_RESOURCES:
                group_edit = QLineEdit(circuit_data.get("GROUP_ID", ""))
                group_edit.setPlaceholderText(f"例如: {circuit}_Group1 (同组将只占用1个物理通道)")
                form.addRow("物理通道复用组 (MUX Group):", group_edit)
                current_editors["GROUP_ID"] = group_edit

            else:
                group_edit = QLineEdit(circuit_data.get("GROUP_ID", ""))
                group_edit.setPlaceholderText("例如: BUF_1")
                vcc_edit = QLineEdit(circuit_data.get("VCC_NET", ""))
                vcc_edit.setPlaceholderText("例如: +5V_VDD")
                
                form.addRow("共享模块组号 (Group):", group_edit)
                form.addRow("模块正电源 (VCC Net):", vcc_edit)
                
                current_editors["GROUP_ID"] = group_edit
                current_editors["VCC_NET"] = vcc_edit

            self.tabs.addTab(tab, circuit)
            self.editors[circuit] = current_editors
        
        btn_box = QHBoxLayout()
        save_btn = QPushButton("💾 保存各模块配置")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 6px; font-weight: bold;")
        save_btn.clicked.connect(self.accept)
        btn_box.addStretch()
        btn_box.addWidget(save_btn)
        self.layout.addLayout(btn_box)
        
    def get_data(self):
        result_dict = {}
        for circuit, edits in self.editors.items():
            circuit_params = {}
            for key, widget in edits.items():
                if isinstance(widget, QLineEdit):
                    val = widget.text().strip()
                    if val: circuit_params[key] = val
                elif isinstance(widget, QComboBox):
                    circuit_params[key] = widget.currentText()
            
            if circuit_params:
                result_dict[circuit] = circuit_params
                
        return json.dumps(result_dict, ensure_ascii=False) if result_dict else "{}"

# ========================================================
# 主界面类
# ========================================================
class Table2SchGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Table2Sch - Smart ATE Hardware Planner (V3.1 Core Fixed)")
        self.resize(1400, 850)
        
        self.tp_pins = []  
        self.slot_map = {} 
        self.channels_per_board = {}
        
        self.connect_types = ["Direct", "Relay", "Kelvin", "NC"] 
        self.active_circuits = get_available_active_circuits()
        self.resource_types = ["FPVIe", "FXVIe", "ACM200", "DCM", "HPSM", "QTMUe"]
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.init_sheet1_project()
        self.init_sheet2_pinmap()
        
    def init_sheet1_project(self):
        tab = QWidget()
        layout = QVBoxLayout() 
        
        # 🌟 动态计算项目根目录 (假设当前文件在 src/gui/main_window.py)
        import os
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_file_dir))
        
        default_hw_path = os.path.join(project_root, "Sch_lib", "platforms", "sts8300_slot.xlsx")
        default_sym_path = os.path.join(project_root, "Sch_lib", "sockets", "JWH6376_SOCKET_PCB.kicad_sym")
        
        gb_proj = QGroupBox("1. Project Setup & Global Defaults")
        lo_proj = QFormLayout()
        self.proj_name = QLineEdit("STS8300_LB_RevA")
        self.sites_le = QLineEdit("4") 
        self.schema_ver_le = QLineEdit("1.0")
        self.def_pkg_le = QLineEdit("0603")
        self.def_vol_le = QLineEdit("50V")
        self.def_tol_le = QLineEdit("1%")
        self.platform_cb = QComboBox()
        self.platform_cb.addItems(["STS8300_A28D4", "V93000"])
        
        hw_layout = QHBoxLayout()
        # 🌟 使用动态生成的绝对路径，并规范化斜杠
        self.hw_config_le = QLineEdit(os.path.normpath(default_hw_path))
        hw_browse_btn = QPushButton("Load Hardware")
        hw_browse_btn.clicked.connect(self.load_hardware_config)
        hw_layout.addWidget(self.hw_config_le)
        hw_layout.addWidget(hw_browse_btn)

        lo_proj.addRow("Project Name:", self.proj_name)
        lo_proj.addRow("Total Sites:", self.sites_le)
        lo_proj.addRow("Schema Version:", self.schema_ver_le)
        lo_proj.addRow("Default Package:", self.def_pkg_le)
        lo_proj.addRow("Default Voltage:", self.def_vol_le)
        lo_proj.addRow("Default Tolerance:", self.def_tol_le)
        lo_proj.addRow("ATE Platform:", self.platform_cb)
        lo_proj.addRow("Hardware Config:", hw_layout)
        gb_proj.setLayout(lo_proj)

        gb_tp = QGroupBox("2. Test Plan (TP) Smart Parser")
        lo_tp = QFormLayout()
        tp_layout = QHBoxLayout()
        self.tp_path_le = QLineEdit()
        self.tp_path_le.setPlaceholderText("Select TP Excel to sync Pin Names first...")
        tp_browse_btn = QPushButton("Upload TP")
        tp_browse_btn.clicked.connect(self.load_tp_data)
        tp_layout.addWidget(self.tp_path_le)
        tp_layout.addWidget(tp_browse_btn)
        self.tp_status_lbl = QLabel("TP Status: No file loaded.")
        self.tp_status_lbl.setStyleSheet("color: gray;")
        lo_tp.addRow("TP Excel Path:", tp_layout)
        lo_tp.addRow(self.tp_status_lbl)
        gb_tp.setLayout(lo_tp)

        gb_sym = QGroupBox("3. Socket Symbol Parser")
        lo_sym = QFormLayout()
        file_layout = QHBoxLayout()
        # 🌟 使用动态生成的绝对路径，并规范化斜杠
        self.sym_path_le = QLineEdit(os.path.normpath(default_sym_path))
        browse_btn = QPushButton("Browse Sym")
        browse_btn.clicked.connect(self.browse_sym_file)
        file_layout.addWidget(self.sym_path_le)
        file_layout.addWidget(browse_btn)

        sym_layout = QHBoxLayout()
        self.target_sym_cb = QComboBox() 
        parse_btn = QPushButton("Parse Socket & Auto-Match TP")
        parse_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        parse_btn.clicked.connect(self.parse_selected_symbol)
        sym_layout.addWidget(QLabel("Target Socket:"))
        sym_layout.addWidget(self.target_sym_cb, stretch=1)
        sym_layout.addWidget(parse_btn)
        
        lo_sym.addRow("Library File:", file_layout)
        lo_sym.addRow("Run Parser:", sym_layout)
        gb_sym.setLayout(lo_sym)
        
        layout.addWidget(gb_proj)
        layout.addWidget(gb_tp)
        layout.addWidget(gb_sym)
        layout.addStretch() 
        tab.setLayout(layout)
        self.tabs.addTab(tab, "1. Project Setup")

    def init_sheet2_pinmap(self):
        tab = QWidget()
        layout = QVBoxLayout()
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Physical Pin (TP Name)", "Logical Net", "Resource Types", 
            "Channel Allocations", "Connect Type", "Active Circuits", "Passives", "Params"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("+ Add Manual Row")
        add_btn.clicked.connect(lambda: self.add_table_row("1", {"Single": "1"}, "Net1", ["ACM200"], "", "Direct", [], "", "{}"))
        
        # 已移除 Import CSV 按钮，保持 UI 原貌
        
        allocate_btn = QPushButton("⚙️ Auto Allocate Channels")
        allocate_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; height: 35px;")
        allocate_btn.clicked.connect(self.auto_allocate_channels)
        
        export_btn = QPushButton("🚀 Export CSV")
        export_btn.clicked.connect(self.export_all_formats)
        
        gen_sch_btn = QPushButton("🎨 Generate KiCad Sch!")
        gen_sch_btn.setStyleSheet("background-color: #9C27B0; color: white; font-weight: bold; height: 35px;")
        gen_sch_btn.clicked.connect(self.generate_schematic)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(allocate_btn)
        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(gen_sch_btn)
        
        layout.addLayout(btn_layout)
        layout.addWidget(self.table)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "2. Pin Mapping")

    def on_cell_double_clicked(self, row, col):
        if col == 7: 
            active_circuits_widget = self.table.cellWidget(row, 5)
            selected_circuits = active_circuits_widget.get_checked_items() if active_circuits_widget else []
            
            resources_widget = self.table.cellWidget(row, 2)
            selected_resources = resources_widget.get_checked_items() if resources_widget else []
            
            configurable_modules = selected_circuits.copy()
            
            for res in ["QTMUe", "FPVIe", "FXVIe", "ACM200", "DCM", "HPSM"]:
                if res in selected_resources:
                    configurable_modules.append(res)
                
            if not configurable_modules:
                QMessageBox.warning(self, "操作提示", "请先选择需要配置参数的模块或硬件资源！")
                return

            item = self.table.item(row, col)
            current_text = item.text() if item else "{}"
            
            dlg = ParamEditorDialog(current_text, configurable_modules, self)
            if dlg.exec_():
                if not item:
                    item = QTableWidgetItem()
                    self.table.setItem(row, col, item)
                item.setText(dlg.get_data())

    def add_table_row(self, display_pin, hidden_pin_dict, net, checked_res_list, chan, conn_type, active_list, passive_str, params):
        row = self.table.rowCount()
        self.table.insertRow(row)
        item_pin = QTableWidgetItem(display_pin)
        item_pin.setData(Qt.UserRole, hidden_pin_dict)
        self.table.setItem(row, 0, item_pin)
        self.table.setItem(row, 1, QTableWidgetItem(net))
        
        res_cb = CheckableComboBox()
        res_cb.addItems(self.resource_types, checked_texts=checked_res_list)
        self.table.setCellWidget(row, 2, res_cb)
        self.table.setItem(row, 3, QTableWidgetItem(chan))
        
        conn_cb = QComboBox()
        conn_cb.addItems(self.connect_types)
        if conn_type not in self.connect_types:
            conn_type = "Direct"
        conn_cb.setCurrentText(conn_type)
        
        self.table.setCellWidget(row, 4, conn_cb)
        
        act_cb = CheckableComboBox()
        act_cb.addItems(self.active_circuits, checked_texts=active_list)
        self.table.setCellWidget(row, 5, act_cb)
        self.table.setCellWidget(row, 6, QLineEdit(passive_str))
        self.table.setItem(row, 7, QTableWidgetItem(params))

    def load_tp_data(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open TP", "", "Excel Files (*.xlsx *.xls)")
        if not file_name: return
        self.tp_path_le.setText(file_name)
        try:
            self.tp_pins = TestPlanParser.parse_tp_pins(file_name)
            self.tp_status_lbl.setText(f"TP Status: ✅ Smart Extracted {len(self.tp_pins)} pins.")
            self.tp_status_lbl.setStyleSheet("color: green; font-weight: bold;")
            for i in range(self.target_sym_cb.count()):
                if "SOCKET" in self.target_sym_cb.itemText(i).upper():
                    self.target_sym_cb.setCurrentIndex(i); break
            QMessageBox.information(self, "TP Parsed", f"Successfully extracted {len(self.tp_pins)} Pins.")
        except Exception as e:
            QMessageBox.critical(self, "TP Error", str(e))

    def parse_selected_symbol(self):
        filepath = self.sym_path_le.text()
        target_sym = self.target_sym_cb.currentText()
        if not filepath or not target_sym: return
        if not self.tp_pins:
            QMessageBox.warning(self, "Warning", "Please upload TP Excel first!"); return
        
        try:
            from parsers.sym_parser import KiCadSymParser
            logical_pads = KiCadSymParser.parse_file(filepath, target_sym)
        except Exception as e:
            QMessageBox.critical(self, "Parse Error", str(e)); return

        if len(logical_pads) != len(self.tp_pins):
            if QMessageBox.warning(self, "Mismatch", f"Symbol: {len(logical_pads)} pins, TP: {len(self.tp_pins)} pins. Continue?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.No: return

        self.table.setRowCount(0)
        
        mapped_data = SmartPinMapper.apply_rules(logical_pads, self.tp_pins)
        for row_data in mapped_data:
            self.add_table_row(
                row_data["display_pin"], row_data["hidden_pin_dict"], row_data["logical_net"],
                row_data["res_defaults"], "", row_data.get("conn_type", "Direct"), row_data["active_circuits"], "", row_data["params"]
            )
        self.tabs.setCurrentIndex(1)

    def load_hardware_config(self):
        filepath = self.hw_config_le.text()
        try:
            from parsers.excel_parser import HardwareExcelParser
            self.slot_map, self.channels_per_board = HardwareExcelParser.parse(filepath)
            QMessageBox.information(self, "Success", "Hardware topology loaded!")
        except Exception as e: 
            QMessageBox.critical(self, "Error", str(e))

    def browse_sym_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open", "", "KiCad (*.kicad_sym)")
        if file_name:
            self.sym_path_le.setText(file_name)
            self.target_sym_cb.clear()
            with open(file_name, 'r', encoding='utf-8') as f:
                syms = re.findall(r'\(symbol\s+"([^"]+)"', f.read())
                self.target_sym_cb.addItems(list(dict.fromkeys([s for s in syms if not re.search(r'_\d+_\d+$', s)])))

    def auto_allocate_channels(self):
        if not self.slot_map:
            QMessageBox.warning(self, "Warning", "Please load Hardware Excel first! (Project Setup 面板)")
            return
            
        try:
            total_sites = int(self.sites_le.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Total Sites must be an integer!")
            return

        table_data = []
        for row in range(self.table.rowCount()):
            res_widget = self.table.cellWidget(row, 2)
            # 采用防御性获取：不仅用接口，如果接口卡了直接截取文字
            resources = res_widget.get_checked_items() if res_widget else []
            if not resources and res_widget and res_widget.currentText():
                resources = [x.strip() for x in res_widget.currentText().split(",") if x.strip()]
            
            try: params = json.loads(self.table.item(row, 7).text() or "{}")
            except: params = {}
            table_data.append({"resources": resources, "params": params, "row_idx": row})

        group_leaders = {} 
        mock_table_data = []
        
        for data in table_data:
            mock_res = []
            for res in data["resources"]:
                group_id = data["params"].get(res, {}).get("GROUP_ID", "")
                if group_id:
                    key = (res, group_id)
                    if key not in group_leaders:
                        group_leaders[key] = {"leader_row": data["row_idx"], "allocations": {}}
                        mock_res.append(res)
                    else:
                        pass
                else:
                    mock_res.append(res)
            mock_table_data.append({"resources": mock_res})

        try:
            from core.scheduler import ChannelScheduler
            allocations = ChannelScheduler.allocate(mock_table_data, total_sites, self.slot_map, self.channels_per_board)
        except Exception as e:
            QMessageBox.critical(self, "Allocation Error", str(e))
            return

        for key, leader_info in group_leaders.items():
            res_name, group_id = key
            leader_row = leader_info["leader_row"]
            alloc_str = allocations[leader_row]
            
            site_allocs = {}
            for block in alloc_str.split('|'):
                block = block.strip()
                m = re.match(r'(Site\d+)\((.*?)\)', block)
                if m:
                    site = m.group(1)
                    inner = m.group(2)
                    for part in inner.split(','):
                        part = part.strip()
                        if part.startswith(res_name + "["):
                            site_allocs[site] = part
            leader_info["allocations"] = site_allocs

        for row_idx, data in enumerate(table_data):
            base_alloc_str = allocations[row_idx]
            final_site_blocks = {f"Site{s}": [] for s in range(1, total_sites + 1)}
            
            for block in base_alloc_str.split('|'):
                block = block.strip()
                if not block: continue
                m = re.match(r'(Site\d+)\((.*?)\)', block)
                if m:
                    final_site_blocks[m.group(1)] = [p.strip() for p in m.group(2).split(',') if p.strip()]
            
            for res in data["resources"]:
                group_id = data["params"].get(res, {}).get("GROUP_ID", "")
                if group_id:
                    key = (res, group_id)
                    if group_leaders[key]["leader_row"] != row_idx:
                        leader_allocs = group_leaders[key]["allocations"]
                        for site, ch_str in leader_allocs.items():
                            if ch_str not in final_site_blocks[site]:
                                final_site_blocks[site].append(ch_str)
                            
            final_str_parts = []
            for s in range(1, total_sites + 1):
                site_key = f"Site{s}"
                if final_site_blocks[site_key]:
                    final_str_parts.append(f"{site_key}({', '.join(final_site_blocks[site_key])})")
                    
            self.table.setItem(row_idx, 3, QTableWidgetItem(" | ".join(final_str_parts)))

        QMessageBox.information(self, "Success", f"Allocated channels for ALL {total_sites} sites (MUX Optimization Applied!)")

    # 🌟 核心防御修复：彻底根除 CSV 漏字 BUG，直接抓取你看到的真实文本！
    # 🌟 核心防御修复：彻底根除 CSV 漏字 BUG，直接抓取你看到的真实文本！
    def _gather_gui_data(self):
        from models.schema import Table2SchConfig, ProjectInfo, PinMappingRow
        import os 
        
        # 1. 获取当前项目的根目录 (从 src/gui/main_window.py 推导)
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_file_dir))
        
        # 2. 🌟 核心优化：尝试将文本框里的绝对路径转化为相对路径
        raw_socket_path = self.sym_path_le.text()
        try:
            # 转化为相对路径，比如 "lib/sockets/JWH6376_SOCKET_PCB.kicad_sym"
            rel_socket_path = os.path.relpath(raw_socket_path, project_root)
            # 统一为正斜杠，防止 Windows/Linux 平台差异导致路径解析失败
            rel_socket_path = rel_socket_path.replace('\\', '/')
        except ValueError:
            # 如果文件不在同一个盘符下 (比如代码在D盘，文件在C盘)，转换会报错，此时退回绝对路径
            rel_socket_path = raw_socket_path

        proj = ProjectInfo(
            project_name=self.proj_name.text(), 
            site_num=int(self.sites_le.text()), 
            schema_version=self.schema_ver_le.text(), 
            default_package=self.def_pkg_le.text(), 
            default_voltage=self.def_vol_le.text(), 
            default_tolerance=self.def_tol_le.text(), 
            ate_platform=self.platform_cb.currentText(), 
            component_overrides={
                'SOCKET_PATH': rel_socket_path,       # 👈 这里存入计算好的相对路径！
                'SOCKET_NAME': self.target_sym_cb.currentText(),
                'GLOBAL_LDO': ""
            }
        )
        
        #内部安全取值函数：如果底层列表拿不到，直接按逗号拆分界面上的文字
        # ... (保留你原来的 _get_safe_items 和后面 rows 的列表推导式逻辑) ...
        
        # 内部安全取值函数：如果底层列表拿不到，直接按逗号拆分界面上的文字
        def _get_safe_items(row, col):
            w = self.table.cellWidget(row, col)
            if not w: return []
            items = w.get_checked_items()
            if not items and w.currentText():
                items = [x.strip() for x in w.currentText().split(",") if x.strip()]
            return items

        rows = [PinMappingRow(
            display_pin=self.table.item(r, 0).text(), 
            socket_pins_map=self.table.item(r, 0).data(Qt.UserRole) or {}, 
            logical_net=self.table.item(r, 1).text(), 
            resources=_get_safe_items(r, 2),  # <--- 使用安全取值！
            allocated_channels=self.table.item(r, 3).text() if self.table.item(r, 3) else "", 
            connect_type=self.table.cellWidget(r, 4).currentText(), 
            active_circuits=_get_safe_items(r, 5), # <--- 使用安全取值！
            passive_circuits=[], 
            parameters=self.table.item(r, 7).text() or "{}"
        ) for r in range(self.table.rowCount())]
        
        return Table2SchConfig(project_info=proj, hardware_config=self.hw_config_le.text(), pin_template_mapping=rows)

    def export_all_formats(self):
        try:
            from exporters.report_gen import ReportGenerator
            config = self._gather_gui_data()
            export_dict = config.model_dump() if hasattr(config, "model_dump") else config.dict()
            msg = ReportGenerator.export_all(export_dict)
            QMessageBox.information(self, "Export Successful", msg)
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def generate_schematic(self):
        try:
            from exporters.sch_generator import SchGenerator
            QMessageBox.information(self, "Success!", f"Schematic generated:\n{SchGenerator.generate_from_config(self._gather_gui_data())}")
        except Exception as e: 
            QMessageBox.critical(self, "Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Table2SchGUI()
    win.show()
    sys.exit(app.exec_())