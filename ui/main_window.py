"""
NetBooster 主窗口界面 - 延迟导入版本
使用 QFluentWidgets 实现 Windows 11 Fluent Design 风格

关键特性：所有 Qt 和 qfluentwidgets 导入都延迟到 MainWindow 初始化时
确保 QApplication 已存在，避免 "Must construct a QApplication before a QWidget" 错误
"""

from typing import List, Dict
from utils.network_utils import (
    scan_network_adapters,
    batch_set_adapter_metrics
)


def create_main_window():
    """工厂函数：创建 MainWindow 实例（此时 QApplication 已存在）"""
    # 延迟导入所有 Qt 和 qfluentwidgets
    from PySide6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox, QCheckBox,
        QFrame, QGraphicsDropShadowEffect, QToolButton, QSizePolicy
    )
    from PySide6.QtCore import Qt, QThread, Signal, Slot, QPoint
    from PySide6.QtGui import QFont, QIcon, QColor
    from qfluentwidgets import PushButton, InfoBar, InfoBarPosition
    
    # ========== 后台工作线程 ==========
    class NetworkWorker(QThread):
        """后台网络操作工作线程"""
        scan_finished = Signal(bool, list, str)
        operation_finished = Signal(bool, str, list)
        operation_started = Signal(str)
        
        def __init__(self):
            super().__init__()
            self.operation_type = None
            self.operation_data = None
        
        def set_scan_operation(self):
            self.operation_type = "scan"
            self.operation_data = None
        
        def set_boost_operation(self, if_indices: List[int]):
            self.operation_type = "boost"
            self.operation_data = if_indices
        
        def set_custom_operation(self, adapter_metrics: List[tuple]):
            self.operation_type = "custom"
            self.operation_data = adapter_metrics
        
        def set_reset_operation(self):
            self.operation_type = "reset"
            self.operation_data = None
        
        def run(self):
            try:
                if self.operation_type == "scan":
                    self._handle_scan()
                elif self.operation_type == "boost":
                    self._handle_boost()
                elif self.operation_type == "custom":
                    self._handle_custom()
                elif self.operation_type == "reset":
                    self._handle_reset()
            except Exception as e:
                print(f"[ERROR] 工作线程异常: {e}")
        
        def _handle_scan(self):
            success, adapters, error_msg = scan_network_adapters()
            self.scan_finished.emit(success, adapters, error_msg)
        
        def _handle_boost(self):
            if_indices = self.operation_data
            self.operation_started.emit(f"正在加速 {len(if_indices)} 个网卡...")
            operations = [(idx, 10, False) for idx in if_indices]
            success, results = batch_set_adapter_metrics(operations)
            success_count = sum(1 for r in results if r["success"])
            message = f"成功加速 {success_count}/{len(if_indices)} 个网卡"
            self.operation_finished.emit(success, message, results)
        
        def _handle_custom(self):
            operations = self.operation_data
            self.operation_started.emit(f"正在应用自定义设置到 {len(operations)} 个网卡...")
            success, results = batch_set_adapter_metrics(operations)
            success_count = sum(1 for r in results if r["success"])
            message = f"成功应用设置到 {success_count}/{len(operations)} 个网卡"
            self.operation_finished.emit(success, message, results)
        
        def _handle_reset(self):
            self.operation_started.emit("正在恢复所有网卡为自动跃点模式...")
            success, adapters, error_msg = scan_network_adapters()
            if not success:
                self.operation_finished.emit(False, "恢复失败: 无法获取网卡列表", [])
                return
            operations = [(adapter["index"], None, True) for adapter in adapters]
            success, results = batch_set_adapter_metrics(operations)
            success_count = sum(1 for r in results if r["success"])
            message = f"成功恢复 {success_count}/{len(operations)} 个网卡到自动跃点模式"
            self.operation_finished.emit(success, message, results)
    
    # ========== 网卡表格组件 ==========
    class NetworkAdapterTableWidget(QTableWidget):
        """网卡列表表格组件"""
        def __init__(self):
            super().__init__()
            self.adapter_indices = []
            self.init_ui()

        def init_ui(self):
            self.setColumnCount(6)
            self.setHorizontalHeaderLabels([
                "选择", "网卡别名", "IPv4 地址", "跃点数状态", "自定义跃点数", "操作"
            ])
            self.verticalHeader().setDefaultSectionSize(50)

            header = self.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            header.setSectionResizeMode(2, QHeaderView.Stretch)
            header.setSectionResizeMode(3, QHeaderView.Stretch)
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

            self.setShowGrid(False)
            self.setAlternatingRowColors(True)
            self.setSelectionBehavior(QTableWidget.SelectRows)
            self.setStyleSheet("""
                QTableWidget {
                    background: rgba(255, 255, 255, 230);
                    border: 1px solid rgba(226, 232, 240, 180);
                    border-radius: 16px;
                    gridline-color: rgba(226, 232, 240, 120);
                    padding: 8px;
                    selection-background-color: rgba(59, 130, 246, 40);
                    selection-color: #0f172a;
                    alternate-background-color: rgba(248, 250, 252, 220);
                }
                QTableWidget::item {
                    padding: 10px 8px;
                    border: none;
                    color: #0f172a;
                }
                QTableWidget::item:hover {
                    background: rgba(219, 234, 254, 120);
                    color: #0f172a;
                }
                QTableWidget::item:selected {
                    background: rgba(191, 219, 254, 190);
                    color: #0f172a;
                }
                QHeaderView::section {
                    background: rgba(248, 250, 252, 245);
                    color: #334155;
                    padding: 12px 10px;
                    border: none;
                    border-bottom: 1px solid rgba(226, 232, 240, 180);
                    font-weight: 600;
                }
                QScrollBar:vertical {
                    background: transparent;
                    width: 10px;
                    margin: 8px 2px 8px 2px;
                }
                QScrollBar::handle:vertical {
                    background: rgba(148, 163, 184, 120);
                    border-radius: 5px;
                    min-height: 24px;
                }
                QScrollBar::handle:vertical:hover {
                    background: rgba(100, 116, 139, 170);
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0;
                }
                QCheckBox {
                    spacing: 8px;
                    color: #334155;
                    padding-left: 6px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border-radius: 5px;
                    border: 1px solid #94a3b8;
                    background: white;
                }
                QCheckBox::indicator:hover {
                    border: 1px solid #3b82f6;
                    background: #f8fbff;
                }
                QCheckBox::indicator:checked {
                    border: 1px solid #2563eb;
                    background: #2563eb;
                    image: none;
                }
                QCheckBox::indicator:checked:hover {
                    border: 1px solid #1d4ed8;
                    background: #1d4ed8;
                }
                QPushButton {
                    background: rgba(255, 255, 255, 235);
                    color: #0f172a;
                    border: 1px solid rgba(226, 232, 240, 220);
                    border-radius: 12px;
                    padding: 10px 16px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(248, 250, 252, 245);
                    border: 1px solid rgba(191, 219, 254, 240);
                }
                QPushButton:pressed {
                    background: rgba(226, 232, 240, 220);
                }
                QPushButton:disabled {
                    background: rgba(248, 250, 252, 180);
                    color: #94a3b8;
                    border: 1px solid rgba(226, 232, 240, 160);
                }
            """)
            self.setSortingEnabled(False)
            self.setEditTriggers(QTableWidget.NoEditTriggers)
        
        def clear_table(self):
            self.setRowCount(0)
            self.adapter_indices = []
        
        def add_adapter_row(self, adapter_info: Dict):
            row = self.rowCount()
            self.insertRow(row)
            self.adapter_indices.append(adapter_info['index'])

            checkbox = QCheckBox()
            checkbox.setStyleSheet("""
                QCheckBox {
                    spacing: 8px;
                    color: #334155;
                    padding-left: 6px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border-radius: 5px;
                    border: 1px solid #94a3b8;
                    background: white;
                }
                QCheckBox::indicator:hover {
                    border: 1px solid #3b82f6;
                    background: #f8fbff;
                }
                QCheckBox::indicator:checked {
                    border: 1px solid #2563eb;
                    background: #2563eb;
                    image: none;
                }
                QCheckBox::indicator:checked:hover {
                    border: 1px solid #1d4ed8;
                    background: #1d4ed8;
                }
            """)
            self.setCellWidget(row, 0, checkbox)

            alias_item = QTableWidgetItem(adapter_info['alias'])
            alias_item.setFlags(alias_item.flags() & ~Qt.ItemIsEditable)
            self.setItem(row, 1, alias_item)

            ipv4 = adapter_info['ipv4']
            if isinstance(ipv4, list):
                ipv4 = ', '.join(ipv4)
            ipv4_item = QTableWidgetItem(str(ipv4))
            ipv4_item.setFlags(ipv4_item.flags() & ~Qt.ItemIsEditable)
            self.setItem(row, 2, ipv4_item)

            is_auto = adapter_info['is_auto']
            metric_status = "自动" if is_auto else f"固定值: {adapter_info['metric']}"
            status_item = QTableWidgetItem(metric_status)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            if is_auto:
                status_item.setBackground(QColor(239, 246, 255))
            self.setItem(row, 3, status_item)

            spinbox = QSpinBox()
            spinbox.setMinimum(1)
            spinbox.setMaximum(9999)
            spinbox.setValue(adapter_info['metric'])
            spinbox.setMinimumWidth(96)
            spinbox.setStyleSheet("margin-left: 10px;")
            self.setCellWidget(row, 4, spinbox)
            self.setItem(row, 5, QTableWidgetItem(""))
        
        def get_selected_adapters(self) -> List[Dict]:
            selected = []
            for row in range(self.rowCount()):
                checkbox = self.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    if_index = self.adapter_indices[row]
                    selected.append({'index': if_index, 'alias': self.item(row, 1).text()})
            return selected
        
        def get_all_adapters(self) -> List[Dict]:
            all_adapters = []
            for row in range(self.rowCount()):
                if_index = self.adapter_indices[row]
                spinbox = self.cellWidget(row, 4)
                metric = spinbox.value() if spinbox else 10
                all_adapters.append({
                    'index': if_index,
                    'alias': self.item(row, 1).text(),
                    'metric': metric
                })
            return all_adapters
        
        def select_all(self):
            for row in range(self.rowCount()):
                checkbox = self.cellWidget(row, 0)
                if checkbox:
                    checkbox.setChecked(True)
        
        def deselect_all(self):
            for row in range(self.rowCount()):
                checkbox = self.cellWidget(row, 0)
                if checkbox:
                    checkbox.setChecked(False)
    
    # ========== 主窗口 ==========
    class MainWindow(QMainWindow):
        """NetBooster 主窗口"""
        def __init__(self):
            super().__init__()
            self.setWindowTitle("NetBooster - Windows 多网卡跃点数并发调度工具")
            self.setWindowIcon(QIcon())
            self.resize(1280, 760)
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
            self._drag_pos = None

            self.worker = NetworkWorker()
            self.connect_worker_signals()
            self.init_ui()
            self.load_adapters()
        
        def connect_worker_signals(self):
            self.worker.scan_finished.connect(self.on_scan_finished)
            self.worker.operation_finished.connect(self.on_operation_finished)
            self.worker.operation_started.connect(self.on_operation_started)
        
        def init_ui(self):
            self.setStyleSheet("background: transparent;")

            central_widget = QWidget()
            central_widget.setStyleSheet("background: transparent;")
            self.setCentralWidget(central_widget)

            root_layout = QVBoxLayout(central_widget)
            root_layout.setContentsMargins(24, 24, 24, 24)
            root_layout.setSpacing(18)

            shell = QFrame()
            shell.setObjectName("shellCard")
            shell_layout = QVBoxLayout(shell)
            shell_layout.setContentsMargins(24, 24, 24, 24)
            shell_layout.setSpacing(16)

            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(36)
            shadow.setOffset(0, 10)
            shadow.setColor(QColor(15, 23, 42, 45))
            shell.setGraphicsEffect(shadow)

            shell.setStyleSheet("""
                QFrame#shellCard {
                    background: rgba(255, 255, 255, 232);
                    border: 1px solid rgba(226, 232, 240, 190);
                    border-radius: 24px;
                }
                QLabel#pageTitle {
                    color: #0f172a;
                }
                QLabel#pageSubtitle {
                    color: #64748b;
                }
                QLabel#statusBadge {
                    background: rgba(239, 246, 255, 240);
                    color: #2563eb;
                    border: 1px solid rgba(191, 219, 254, 220);
                    border-radius: 14px;
                    padding: 8px 14px;
                    font-weight: 600;
                }
                QLineEdit, QSpinBox, QComboBox {
                    background: rgba(255, 255, 255, 245);
                    border: 1px solid rgba(226, 232, 240, 200);
                    border-radius: 12px;
                    padding: 8px 10px;
                    color: #0f172a;
                }
                QSpinBox::up-button, QSpinBox::down-button {
                    width: 0px;
                    border: none;
                    background: transparent;
                }
                QCheckBox {
                    spacing: 8px;
                    color: #334155;
                }
            """)

            title_bar = QHBoxLayout()
            title_bar.setContentsMargins(0, 0, 0, 0)
            title_bar.setSpacing(8)

            title_box = QVBoxLayout()
            title_box.setSpacing(4)

            self.refresh_btn = QToolButton()
            self.refresh_btn.setText("↻")
            self.refresh_btn.setFixedSize(36, 32)
            self.refresh_btn.setStyleSheet("""
                QToolButton {
                    background: rgba(255, 255, 255, 220);
                    color: #334155;
                    border: 1px solid rgba(226, 232, 240, 220);
                    border-radius: 10px;
                    font-size: 18px;
                    font-weight: 600;
                }
                QToolButton:hover {
                    background: rgba(239, 246, 255, 240);
                    border: 1px solid rgba(191, 219, 254, 240);
                }
            """)
            self.refresh_btn.clicked.connect(self.load_adapters)

            self.min_btn = QToolButton()
            self.min_btn.setText("—")
            self.min_btn.setFixedSize(36, 32)
            self.min_btn.setStyleSheet("""
                QToolButton {
                    background: rgba(255, 255, 255, 220);
                    color: #334155;
                    border: 1px solid rgba(226, 232, 240, 220);
                    border-radius: 10px;
                    font-size: 18px;
                    font-weight: 600;
                }
                QToolButton:hover {
                    background: rgba(239, 246, 255, 240);
                    border: 1px solid rgba(191, 219, 254, 240);
                }
            """)
            self.min_btn.clicked.connect(self.showMinimized)

            self.close_btn = QToolButton()
            self.close_btn.setText("×")
            self.close_btn.setFixedSize(36, 32)
            self.close_btn.setStyleSheet("""
                QToolButton {
                    background: rgba(255, 255, 255, 220);
                    color: #334155;
                    border: 1px solid rgba(226, 232, 240, 220);
                    border-radius: 10px;
                    font-size: 18px;
                    font-weight: 600;
                }
                QToolButton:hover {
                    background: rgba(254, 242, 242, 240);
                    border: 1px solid rgba(248, 113, 113, 220);
                    color: #b91c1c;
                }
            """)
            self.close_btn.clicked.connect(self.close)

            title_bar.addWidget(self.min_btn)
            title_bar.addWidget(self.close_btn)

            title_label = QLabel("NetBooster")
            title_label.setObjectName("pageTitle")
            title_font = QFont()
            title_font.setPointSize(22)
            title_font.setBold(True)
            title_label.setFont(title_font)

            subtitle_label = QLabel("浅色现代界面 · 网卡跃点数管理")
            subtitle_label.setObjectName("pageSubtitle")
            subtitle_font = QFont()
            subtitle_font.setPointSize(10)
            subtitle_label.setFont(subtitle_font)

            title_box.addWidget(title_label)
            title_box.addWidget(subtitle_label)

            self.status_label = QLabel("状态: 正在加载网卡...")
            self.status_label.setObjectName("statusBadge")
            self.status_label.setAlignment(Qt.AlignCenter)

            title_bar.addLayout(title_box)
            title_bar.addStretch()
            title_bar.addWidget(self.status_label)
            title_bar.addWidget(self.refresh_btn)
            title_bar.addWidget(self.min_btn)
            title_bar.addWidget(self.close_btn)
            shell_layout.addLayout(title_bar)

            self.table_widget = NetworkAdapterTableWidget()
            shell_layout.addWidget(self.table_widget)

            action_layout = QHBoxLayout()
            action_layout.setSpacing(12)

            self.select_all_btn = PushButton("全选")
            self.select_all_btn.setMinimumHeight(42)
            self.select_all_btn.setMaximumWidth(100)
            self.select_all_btn.clicked.connect(self.on_select_all_clicked)

            self.deselect_all_btn = PushButton("取消全选")
            self.deselect_all_btn.setMinimumHeight(42)
            self.deselect_all_btn.setMaximumWidth(100)
            self.deselect_all_btn.clicked.connect(self.on_deselect_all_clicked)

            self.boost_btn = PushButton("一键加速")
            self.boost_btn.setMinimumHeight(42)
            self.boost_btn.setMaximumWidth(120)
            self.boost_btn.clicked.connect(self.on_boost_clicked)
            self.boost_btn.setEnabled(False)
            self.boost_btn.setStyleSheet(self._button_style("#2563eb", "#1d4ed8"))

            self.apply_btn = PushButton("应用设置")
            self.apply_btn.setMinimumHeight(42)
            self.apply_btn.setMaximumWidth(120)
            self.apply_btn.clicked.connect(self.on_apply_custom_clicked)
            self.apply_btn.setEnabled(False)
            self.apply_btn.setStyleSheet(self._button_style("#ffffff", "#dbeafe", text_color="#0f172a"))

            self.reset_btn = PushButton("恢复默认")
            self.reset_btn.setMinimumHeight(42)
            self.reset_btn.setMaximumWidth(120)
            self.reset_btn.clicked.connect(self.on_reset_clicked)
            self.reset_btn.setEnabled(False)
            self.reset_btn.setStyleSheet(self._button_style("#ffffff", "#dbeafe", text_color="#0f172a"))

            action_layout.addWidget(self.select_all_btn)
            action_layout.addWidget(self.deselect_all_btn)
            action_layout.addStretch()
            action_layout.addWidget(self.boost_btn)
            action_layout.addWidget(self.apply_btn)
            action_layout.addWidget(self.reset_btn)

            shell_layout.addLayout(action_layout)
            root_layout.addWidget(shell)

            self._InfoBar = InfoBar
            self._InfoBarPosition = InfoBarPosition
            self._Qt = Qt

        def mousePressEvent(self, event):
            if event.button() == Qt.LeftButton:
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
            else:
                super().mousePressEvent(event)

        def mouseMoveEvent(self, event):
            if event.buttons() & Qt.LeftButton and self._drag_pos is not None:
                self.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()
            else:
                super().mouseMoveEvent(event)

        def mouseReleaseEvent(self, event):
            self._drag_pos = None
            super().mouseReleaseEvent(event)

        def _button_style(self, background: str, hover: str, text_color: str = "#ffffff") -> str:
            return f"""
                QPushButton {{
                    background: {background};
                    color: {text_color};
                    border: 1px solid rgba(148, 163, 184, 120);
                    border-radius: 12px;
                    padding: 10px 16px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: {hover};
                    border: 1px solid rgba(96, 165, 250, 180);
                }}
                QPushButton:pressed {{
                    background: rgba(226, 232, 240, 220);
                }}
                QPushButton:disabled {{
                    background: rgba(248, 250, 252, 180);
                    color: #94a3b8;
                    border: 1px solid rgba(226, 232, 240, 160);
                }}
            """

        def load_adapters(self):
            self.table_widget.clear_table()
            self.status_label.setText("状态: 正在加载网卡...")
            self.boost_btn.setEnabled(False)
            self.apply_btn.setEnabled(False)
            self.reset_btn.setEnabled(False)
            self.refresh_btn.setEnabled(False)

            if self.worker.isRunning():
                self.worker.wait()

            self.worker.set_scan_operation()
            self.worker.start()
        
        @Slot(bool, list, str)
        def on_scan_finished(self, success: bool, adapters: list, error_msg: str):
            if success:
                if not adapters:
                    self.status_label.setText("状态: 未找到可用的网卡")
                    self.show_warning("未找到任何可用的网卡")
                else:
                    for adapter in adapters:
                        self.table_widget.add_adapter_row(adapter)
                    self.status_label.setText(f"状态: 已加载 {len(adapters)} 个网卡，就绪")
                    self.boost_btn.setEnabled(True)
                    self.apply_btn.setEnabled(True)
                    self.reset_btn.setEnabled(True)
                    self.refresh_btn.setEnabled(True)
            else:
                self.status_label.setText("状态: 加载失败")
                self.refresh_btn.setEnabled(True)
                self.show_error(f"加载网卡失败:\n\n{error_msg}")
        
        @Slot(str)
        def on_operation_started(self, message: str):
            self.status_label.setText(f"状态: {message}")
            self.boost_btn.setEnabled(False)
            self.apply_btn.setEnabled(False)
            self.reset_btn.setEnabled(False)
        
        @Slot(bool, str, list)
        def on_operation_finished(self, success: bool, message: str, results: list):
            self.boost_btn.setEnabled(True)
            self.apply_btn.setEnabled(True)
            self.reset_btn.setEnabled(True)
            self.refresh_btn.setEnabled(True)

            if success:
                self.status_label.setText(f"状态: {message}")
                self.show_success(message)
                self.load_adapters()
            else:
                self.status_label.setText("状态: 操作失败")
                self.show_error(message)
        
        def on_select_all_clicked(self):
            self.table_widget.select_all()
        
        def on_deselect_all_clicked(self):
            self.table_widget.deselect_all()
        
        def on_boost_clicked(self):
            selected = self.table_widget.get_selected_adapters()
            if not selected:
                self.show_warning("请先选择要加速的网卡")
                return
            if self.worker.isRunning():
                return
            if_indices = [adapter['index'] for adapter in selected]
            self.worker.set_boost_operation(if_indices)
            self.worker.start()
        
        def on_apply_custom_clicked(self):
            all_adapters = self.table_widget.get_all_adapters()
            if not all_adapters:
                self.show_warning("表格中没有网卡数据")
                return
            if self.worker.isRunning():
                return
            operations = [(adapter['index'], adapter['metric'], False) for adapter in all_adapters]
            self.worker.set_custom_operation(operations)
            self.worker.start()
        
        def on_reset_clicked(self):
            if self.worker.isRunning():
                return
            self.worker.set_reset_operation()
            self.worker.start()
        
        def show_info(self, message: str):
            self._InfoBar.info(
                title="提示", content=message, orient=self._Qt.Horizontal,
                position=self._InfoBarPosition.TOP, duration=2000
            )
        
        def show_success(self, message: str):
            self._InfoBar.success(
                title="成功", content=message, orient=self._Qt.Horizontal,
                position=self._InfoBarPosition.TOP, duration=2000
            )
        
        def show_warning(self, message: str):
            self._InfoBar.warning(
                title="警告", content=message, orient=self._Qt.Horizontal,
                position=self._InfoBarPosition.TOP, duration=2000
            )
        
        def show_error(self, message: str):
            self._InfoBar.error(
                title="错误", content=message, orient=self._Qt.Horizontal,
                position=self._InfoBarPosition.TOP, duration=3000
            )
    
    return MainWindow()
