from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout, QMessageBox, QFileDialog, QComboBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime


class AnalyticsDialog(QDialog):
    def __init__(self, parent=None, rows=None, task_results=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Analytics")
        self.resize(800, 600)

        self.rows = rows or []
        self.task_results = task_results or {}

        self.layout = QVBoxLayout(self)
        
        # Выбор типа графика
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["BarChart", "LineChart", "PieChart"])
        self.chart_type_combo.currentIndexChanged.connect(self.update_chart)
        self.layout.addWidget(self.chart_type_combo)

        # Фильтрация по статусу
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["Все", "✅ Success", "❌ ERROR", "⏳ In Progress", "⏸️ Stopped"])
        self.status_filter_combo.currentIndexChanged.connect(self.update_chart)
        self.layout.addWidget(self.status_filter_combo)
        
        self.canvas = FigureCanvas(Figure(figsize=(6, 4)))
        self.layout.addWidget(self.canvas)

        # Bottom buttons
        btn_layout = QHBoxLayout()

        self.save_button = QPushButton("💾 Save Chart")
        self.save_button.setEnabled(False)  # пока график не построен
        btn_layout.addWidget(self.save_button)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        btn_layout.addWidget(self.close_button)

        self.layout.addLayout(btn_layout)

        # Построим первый график (заглушка)
        self.update_chart()
        
        # Save graphic to png
        self.save_button.clicked.connect(self.save_chart)

    def plot_placeholder(self):
        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)
        ax.clear()
        ax.set_title("Analytics Placeholder")
        ax.plot([1, 2, 3], [2, 4, 1])  # временная заглушка
        ax.grid(True)
        self.canvas.draw()
        self.save_button.setEnabled(True)
        
    def plot_bar_chart(self, rows):
        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)
        ax.clear()

        labels = []
        counts = []

        for row in self.rows:
            task = self.task_results.get(row)
            if not task:
                continue

            url = task.get("url", f"Row {row}")
            results = task.get("results", [])

            short_label = url.replace("https://", "").replace("http://", "")
            if len(short_label) > 25:
                short_label = short_label[:25] + "..."

            labels.append(short_label)
            counts.append(len(results))

        if not labels:
            ax.text(0.5, 0.5, "No data to show", ha="center", va="center", fontsize=12)
        else:
            ax.bar(labels, counts, color="skyblue")
            ax.set_title("Number of results by tasks")
            ax.set_ylabel("Elements finded")
            ax.set_xticklabels(labels, rotation=30, ha="right")

        ax.grid(True)
        self.canvas.draw()
        self.save_button.setEnabled(True)
        
    def save_chart(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save graphic in PNG",
            "chart.png",
            "PNG Files (*.png)"
        )

        if not file_path:
            return  # пользователь отменил

        try:
            self.canvas.figure.savefig(file_path, format="png")
            QMessageBox.information(self, "Done", f"Graphic saved in:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "ERROR", f"Failed to save graphic:\n{str(e)}")
            
    def update_chart(self):
        chart_type = self.chart_type_combo.currentText()
        selected_status = self.status_filter_combo.currentText()

        # Фильтрация по статусу
        filtered_rows = []
        for row in self.rows:
            task = self.task_results.get(row)
            if not task:
                continue

            status = task.get("status", "")
            if selected_status == "All" or selected_status in status:
                filtered_rows.append(row)

        # Выбор графика
        if chart_type == "BarChart":
            self.plot_bar_chart(filtered_rows)
        elif chart_type == "LineChart":
            self.plot_line_chart(filtered_rows)
        elif chart_type == "PieChart":
            self.plot_pie_chart(filtered_rows)
            
    def plot_line_chart(self, rows):
        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)
        ax.clear()

        times = []
        counts = []
        labels = []

        for row in rows:
            task = self.task_results.get(row)
            print("ROW:", row)
            print("last_run =", task.get("last_run"))
            if not task:
                continue

            last_run = task.get("last_run")
            results = task.get("results", [])

            if not last_run or not results:
                continue

            try:
                time_obj = datetime.strptime(last_run, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

            times.append(time_obj)
            counts.append(len(results))

            url = task.get("url", f"Row {row}")
            short = url.replace("https://", "").replace("http://", "")
            short = short[:25] + "..." if len(short) > 25 else short
            labels.append(short)

        if not times:
            ax.text(0.5, 0.5, "No data for graphic", ha="center", va="center")
        else:
            ax.plot(times, counts, marker="o", color="green")
            ax.set_title("Startup time results")
            ax.set_xlabel("Time")
            ax.set_ylabel("Number of elements found")
            ax.grid(True)

        self.canvas.draw()
        self.save_button.setEnabled(True)
        
    
    def plot_pie_chart(self, rows):
        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)

        status_counts = {}

        for row in rows:
            task = self.task_results.get(row)
            if not task:
                continue
            status = task.get("status", "Unknown").strip()
            status_counts[status] = status_counts.get(status, 0) + 1

        if not status_counts:
            ax.text(0.5, 0.5, "No data to plot chart", ha="center", va="center")
        else:
            labels = list(status_counts.keys())
            sizes = list(status_counts.values())

            ax.pie(
                sizes,
                labels=labels,
                autopct="%1.1f%%",
                startangle=90,
                wedgeprops=dict(edgecolor='white')
            )
            ax.set_title("Distribution of tasks by status")

        self.canvas.draw()
        self.save_button.setEnabled(True)





