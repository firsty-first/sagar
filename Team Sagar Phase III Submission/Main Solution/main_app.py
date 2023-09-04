import sys
import os
import shutil
from ultralytics import YOLO
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QLabel, QSpacerItem, QSizePolicy, QFileDialog, QScrollArea, QTableWidget, QTableWidgetItem, QGridLayout, QTabWidget
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtCore import Qt, QSize, pyqtSignal,QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
import pandas as pd
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
from geopy.geocoders import Nominatim
import folium
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist
from geopy.distance import great_circle
import geopy.distance
import threading
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QPushButton
from PyQt5.QtGui import QImage, QImageReader, QImageWriter
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QGraphicsView, QGraphicsScene,QMessageBox,QApplication
from PyQt5.QtGui import QPixmap, QImageReader, QImageWriter, QPainter
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QWheelEvent
import time
from pyqtspinner.spinner import WaitingSpinner
from PyQt5.QtGui import QColor, QPalette





script_directory = os.path.dirname(os.path.abspath(__file__)) #changing the directory to the script directory
os.chdir(script_directory)
#os.environ['QT_QPA_FONTDIR'] = 'font.ttf'
model = YOLO('Finalmodel.onnx', task='detect') #defining the model path and its task
#model=YOLO('Finalmodel.pt',task='detect')
dir_of_images = []  
def calculate_distance(coord1, coord2):                     #it is used to measure the distance between two coordinates
    return geopy.distance.distance(coord1, coord2).km


def plot_coordinates_on_map(df):
    m = folium.Map(location=df['cordinates'][0], zoom_start=15)
    for index, row in df.iterrows():
        coordinate = row['cordinates']
        count = row['Plastic Count']
        nearest_land = row['Nearest Land']
        image=os.path.basename(row['Image'])
        folium.Marker(
            location=coordinate,
            popup=f'Image: {image}\nCount: {count},\nNearest land:{nearest_land} ',  # Label with the count value
            icon=folium.Icon(icon='cloud'),
            sticky=True
            ).add_to(m)
        m.save('plastic_count_map.html')

# Create a list to store the nearest person's information for each image
nearest_person_info = []


df3=pd.read_csv('contacts.csv') #reading the contact CSV File
def dir_if_exist(path):
    try:
        shutil.rmtree(path)
    except:
        pass

def generate_geo_tag_url(latitude, longitude):
    url = f"https://www.google.com/maps?q={latitude},{longitude}"
    return url




def find_nearest_land(coord):
    # Initialize the Nominatim geocoder
    geolocator = Nominatim(user_agent="nearest_place_finder")

    # Reverse geocode the given coordinates to get the place information
    location = geolocator.reverse(coord, exactly_one=True)

    if location:
        place_type = location.raw.get('type', 'Unknown')
        place_id = location.raw.get('place_id', 'Unknown')
        place_name = location.address
        place_coord = (location.latitude, location.longitude)
        return place_type, place_id, place_name, place_coord
    else:
        return None

def get_date_taken(image_path):
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()

        # Iterate through all the Exif tags
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            if tag_name == "DateTimeOriginal":
                return value

        # If the "DateTimeOriginal" tag is not found, return None
        return 0
    except:
        pass

def get_Geo_tag(path):
    image = Image.open(path)
    exif_data = image._getexif()
    gps_info = exif_data[34853]
    latitude = float(gps_info[2][0]) + float(gps_info[2][1]) / 60 + float(gps_info[2][2]) / 3600
    longitude = float(gps_info[4][0]) + float(gps_info[4][1]) / 60 + float(gps_info[4][2]) / 3600
    return latitude, longitude





dir_if_exist('runs')


class ImageDisplayWindow(QDialog):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Image Viewer")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: rgb(68, 70, 84);")

        self.layout = QVBoxLayout()

        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.image_path = image_path
        self.display_image()

        self.layout.addWidget(self.view)
        self.setLayout(self.layout)

        # Enable standard mouse wheel zooming
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setInteractive(True)

    def display_image(self):
        pixmap = QPixmap(self.image_path)
        item = self.scene.addPixmap(pixmap)
        self.view.setScene(self.scene)
        self.view.fitInView(item, Qt.KeepAspectRatio)

    def wheelEvent(self, event: QWheelEvent):
        # Zoom in/out using the mouse wheel
        zoom_factor = 1.15  # You can adjust the zoom factor as needed
        if event.angleDelta().y() > 0:
            self.view.scale(zoom_factor, zoom_factor)
        else:
            self.view.scale(1.0 / zoom_factor, 1.0 / zoom_factor)


class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

class AspectRatioGraphicsView(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)


from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt5.QtGui import QColor, QPalette

class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Loading")
        self.setFixedSize(200, 100)
        self.layout = QVBoxLayout(self)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.spinner = WaitingSpinner(self)
        self.spinner.start()
        #self.label = QLabel("Processing Complete \nNow You can click on the \nshow process image \nbutton to show the results ", self)
        self.label = QLabel("Processing Images Please Wait ", self)
        self.layout.addWidget(self.spinner)
        self.layout.addWidget(self.label)







class MainWindow(QMainWindow):

    done_signal = pyqtSignal()
    

    def __init__(self):
        super().__init__()
        # data_processing_finished_signal = pyqtSignal()


        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        #self.setFixedSize(800, 600)
        self.done_signal.connect(self.close_loading_dialog)
        

        self.layout = QHBoxLayout()
        self.central_widget.setLayout(self.layout)
        #self.layout.setContentsMargins(0, 0, 0, 0)
        self.data_loading_thread=None
        #change regarding thread timing
        self.thread_status_timer=QTimer(self)
        self.thread_status_timer.timeout.connect(self.check_thread_status)
        self.thread_status_timer.start(500)
        #self.data_processing_finished_signal.connect(self.on_data_processing_finished)


        self.sidebar = QWidget(self)
        self.sidebar.setMinimumWidth(150)
        self.sidebar.setStyleSheet("background-color: rgb(52, 54, 65);")

        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setAlignment(Qt.AlignTop)
        self.sidebar_layout.setContentsMargins(0, 0, 0, 15)

        self.layout.addWidget(self.sidebar)
        self.loading_dialog = None

        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.setStyleSheet("background-color: rgb(68, 70, 84);")
        self.layout.addWidget(self.stacked_widget)

        self.home_button = QPushButton("Home", self)
        self.load_image_button = QPushButton("Load Image", self)
        self.process_image_button = QPushButton("Show Processed Images", self)
        self.contact_button = QPushButton("Contact Database", self)
        self.generate_result_button = QPushButton("Generate Result", self)

        button_style = (
            "QPushButton { background-color: rgb(25, 195, 125); color: white; border: none; padding: 10px; }"
            "QPushButton:hover { background-color: rgb(35, 205, 135); }"
            "QPushButton:pressed { background-color: rgb(15, 175, 105); }"
        )

        self.home_button.setStyleSheet(button_style)
        self.load_image_button.setStyleSheet(button_style)
        self.process_image_button.setStyleSheet(button_style)
        self.contact_button.setStyleSheet(button_style)
        self.generate_result_button.setStyleSheet(button_style)

        self.sidebar_layout.addWidget(self.home_button)
        self.sidebar_layout.addWidget(self.load_image_button)
        self.sidebar_layout.addWidget(self.process_image_button)
        self.sidebar_layout.addWidget(self.contact_button)
        self.sidebar_layout.addWidget(self.generate_result_button)

        self.sidebar_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.home_button.clicked.connect(self.show_home)
        self.load_image_button.clicked.connect(self.show_load_image)
        self.process_image_button.clicked.connect(self.show_process_image)
        self.contact_button.clicked.connect(self.show_contact_database)
        self.generate_result_button.clicked.connect(self.show_generate_result)

        # Create the home screen layout
        self.home_screen_layout = QHBoxLayout()
        self.home_screen_widget = QWidget()
        self.home_screen_widget.setLayout(self.home_screen_layout)

        self.loading_label = QLabel(self)
        self.loading_movie = QMovie("loading.gif")  # Replace with the path to your loading GIF
        self.loading_label.setMovie(self.loading_movie)
        self.loading_label.hide()

        # Welcome message and instructions label
        welcome_label = QLabel("Welcome to the Application!\n\nInstructions:\n1. Click the 'Load Image' button to go to load screen.\n2. Click the 'load' button to upload images.\n3. Click the 'Next' button to process the images.\n4. Click the 'Show Process Image' button to go to \n   process screen.\n5. Click the 'Contact Database' button to view the contact\n6. Click the 'Generate Result' button to view the result\n7. There will be three tabs which will  display\n  the useful  extracted data including the folium map\n\n\n\n\n\n\n\nNote:\n1. The 'Process Image' and 'Generate Result' buttons will only work after\n  you have uploaded and processed the images.\n2.The last set of processed images will be saved \n   into the directory'runs/predict/Images\n3.In the contact database the numbers \n  and names are taken imaginary to \n  demonstrate the working of the software.\n4. By just replacing the contact.csv with a real data \n with same name and file format,\n will be completely ready to work on real world.\n5. In the result tables you can adjust \n the width of each coloumn shell if require to view \n the commplete cell in one line ", self)
        welcome_label.setStyleSheet("color: white; font-size: 16px;")        
        self.home_screen_layout.addWidget(welcome_label, alignment=Qt.AlignLeft | Qt.AlignTop)

        # Load and display the welcome image on the right side
        welcome_image_label = QLabel(self)
        welcome_image_pixmap = QPixmap("welcome.png")  # Replace with your image path
        welcome_image_pixmap = welcome_image_pixmap.scaled(QSize(200, 200), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        welcome_image_label.setPixmap(welcome_image_pixmap)
        welcome_image_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.home_screen_layout.addWidget(welcome_image_label, alignment=Qt.AlignTop)


        # Set the home screen as the first screen
        self.stacked_widget.addWidget(self.home_screen_widget)

        # Load screen
        self.load_screen_layout = QVBoxLayout()
        self.load_screen_widget = QWidget()
        self.load_screen_widget.setLayout(self.load_screen_layout)

        # Load button and next button
        self.load_button = QPushButton("Load", self)
        self.load_button.setStyleSheet(button_style)
        self.next_button = QPushButton("Next", self)
        self.next_button.setStyleSheet(button_style)
        self.load_button.setFixedSize(self.home_button.sizeHint())
        self.next_button.setFixedSize(self.home_button.sizeHint())

        self.load_screen_buttons_layout = QHBoxLayout()
        self.load_screen_buttons_layout.addWidget(self.load_button, alignment=Qt.AlignLeft)
        self.load_screen_buttons_layout.addWidget(self.next_button, alignment=Qt.AlignRight)
        self.load_screen_layout.addLayout(self.load_screen_buttons_layout)

        # Scroll area for thumbnails
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setMaximumHeight(600)
        self.scroll_area.setStyleSheet("background-color: rgb(52, 53, 65);")
        self.thumbnail_container = QWidget(self.scroll_area)
        self.thumbnail_grid_layout = QGridLayout(self.thumbnail_container)

        self.scroll_area.setWidget(self.thumbnail_container)
        self.scroll_area.setWidgetResizable(True)

        self.load_screen_layout.addWidget(self.scroll_area)
        # self.load_screen_layout.addSpacerItem(QSpacerItem(4,4, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.stacked_widget.addWidget(self.load_screen_widget)

        # Process screen
        self.process_screen_layout = QGridLayout()
        self.process_screen_widget = QWidget()
        self.process_screen_widget.setLayout(self.process_screen_layout)

        self.process_screen_scroll_area = QScrollArea(self)
        self.process_screen_scroll_area.setWidgetResizable(True)
        self.process_screen_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.process_screen_scroll_area.setWidget(self.process_screen_widget)

        self.stacked_widget.addWidget(self.process_screen_scroll_area)

        # Contact screen
        self.contact_screen_layout = QVBoxLayout()
        self.contact_screen_widget = QWidget()
        self.contact_screen_widget.setLayout(self.contact_screen_layout)
        self.stacked_widget.addWidget(self.contact_screen_widget)

        # Result screen
        self.result_screen_tab_widget = QTabWidget(self)
        self.result_screen_tab_widget.setStyleSheet(
            "QTabWidget::pane { background-color: rgb(68, 70, 84); color: white; }"
            "QTabBar::tab { background-color: rgb(52, 54, 65); color: white; }"
            "QTabBar::tab:selected { background-color: rgb(25, 195, 125); }"
        )

        self.result1_tab = QWidget()
        self.result2_tab = QWidget()
        self.map_tab = QWidget()

        self.result_screen_tab_widget.addTab(self.result1_tab, "Output CSV")
        self.result_screen_tab_widget.addTab(self.result2_tab, "Output1 CSV")
        self.result_screen_tab_widget.addTab(self.map_tab, "Folium Map")

        self.result_screen_layout = QVBoxLayout(self.result1_tab)
        self.result1_table = QTableWidget(self.result1_tab)
        self.result1_table.setStyleSheet("color: white; background-color: rgb(68, 70, 84);")
        self.result_screen_layout.addWidget(self.result1_table)
        

        self.result2_screen_layout = QVBoxLayout(self.result2_tab)
        self.result2_table = QTableWidget(self.result2_tab)
        self.result2_table.setStyleSheet("color: white; background-color: rgb(68, 70, 84);")
        self.result2_screen_layout.addWidget(self.result2_table)
        

        self.map_tab.layout = QVBoxLayout(self.map_tab)
        self.map_view = QWebEngineView()
        self.map_view.load(QUrl.fromLocalFile(os.path.abspath("plastic_count_map.html")))
        self.map_tab.layout.addWidget(self.map_view)
        self.stacked_widget.addWidget(self.result_screen_tab_widget)
        self.stacked_widget.addWidget(QLabel("Result Screen"))
        self.stacked_widget.setCurrentIndex(0)
        self.load_button.clicked.connect(self.load_images)
        self.next_button.clicked.connect(self.next_image)
        


    #change checkpoints 8
    def check_thread_status(self):
        if self.data_loading_thread and not self.data_loading_thread.is_alive():
            self.thread_status_timer.stop()

    def open_image_display(self, image_path):
        image_display = ImageDisplayWindow(image_path)
        image_display.exec_()  # This blocks until the image display window is closed







          
    def show_home(self):
        self.stacked_widget.setCurrentIndex(0)

    def show_load_image(self):
        self.stacked_widget.setCurrentIndex(1)

    def show_process_image(self):
        self.stacked_widget.setCurrentIndex(2)
        

    def show_contact_database(self):
        self.stacked_widget.setCurrentIndex(3)
        default_contact_file = "contacts.csv"  # Replace with the actual path
        self.display_contact_csv(default_contact_file)




    def count_plastic_from_image(self, path):
        load = model.predict(path, save=True, imgsz=1024, conf=0.420)
        count = len(load[0])
        return count
    def next_image(self):


        if self.data_loading_thread is None or not self.data_loading_thread.is_alive():
            self.loading_label.show()
            self.loading_movie.start()
            

            
            self.data_loading_thread = threading.Thread(target=self.load_and_process_data)
            self.data_loading_thread.start()

        self.load_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.process_image_button.setEnabled(False)
        self.generate_result_button.setEnabled(False)
        self.loading_dialog = LoadingDialog(self)
        self.loading_dialog.exec_()
        self.change()
    
    def change(self):
        self.populate_processed_images()
        self.stacked_widget.setCurrentIndex(2)
        

    
    def on_data_processing_finished(self):
        if self.loading_dialog:
            self.loading_dialog.accept()
    # Additional UI updates here...

    
    
    def load_images(self):

        global df
        global df2
        df = pd.DataFrame(columns=['Image', 'Plastic Count', 'Date Taken', 'cordinates', 'Geo Tag', 'Nearest Land', 'Distance'])
        df2 = pd.DataFrame(columns=['Image', 'count', 'name', 'distance', 'contact', 'Geo_tag_url'])
        dir_if_exist('runs')
        nearest_person_info.clear()
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        image_paths, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)", options=options)

        for i in reversed(range(self.thumbnail_grid_layout.count())):
            widget = self.thumbnail_grid_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
                
        max_col = 4
        current_col = 0
        current_row = 0
        thumbnail_size = QSize(150,150)
        self.loaded_image_paths = []
        for image_path in image_paths:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(thumbnail_size, Qt.KeepAspectRatio)
                thumbnail_label = QLabel()
                thumbnail_label.setPixmap(pixmap)
                self.thumbnail_grid_layout.addWidget(thumbnail_label, current_row, current_col)
                current_col += 1
                if current_col >= max_col:
                    current_col = 0
                    current_row += 1
                self.loaded_image_paths.append(image_path)
                latitude, longitude = get_Geo_tag(image_path)
            else:
            # Handle the case where the pixmap couldn't be loaded
                print(f"Failed to load image: {image_path}")

            
        # loading_dialog = LoadingDialog(self)
        
        # loading_dialog.exec_()


    # Refresh the layout to display the loaded images
        self.thumbnail_grid_layout.update()

    def load_and_process_data(self):     
        df['Image'] = self.loaded_image_paths
        df['Plastic Count'] = [self.count_plastic_from_image(path) for path in self.loaded_image_paths]
        df['Date Taken'] = [get_date_taken(path) for path in self.loaded_image_paths]
        #df['Cordinates'] = [f"{get_Geo_tag(path)[0] for path in self.loaded_image_paths},{get_Geo_tag(path)[1] for path in self.loaded_image_paths}"]
        df['cordinates'] = [get_Geo_tag(path) for path in self.loaded_image_paths]
        df['Geo Tag'] = [generate_geo_tag_url(get_Geo_tag(path)[0], get_Geo_tag(path)[1]) for path in self.loaded_image_paths]
    
        df['Nearest Land'] = [find_nearest_land(get_Geo_tag(path)) for path in self.loaded_image_paths]
        df['Distance'] = [geodesic(get_Geo_tag(path), find_nearest_land(get_Geo_tag(path))[3]).miles for path in self.loaded_image_paths]

        for index, row in df.iterrows():
            
            image_coords = row['cordinates']  # Convert the string to a tuple
            min_distance = float('inf')
            nearest_person = None
            
            for _, contact_row in df3.iterrows():
                contact_coords = eval(contact_row['Coordinates'])  # Convert the string to a tuple
                distance = calculate_distance(image_coords, contact_coords)
                if distance < min_distance:
                    min_distance = distance
                    nearest_person = {
                        'Image': os.path.basename(row['Image']),
                        'count': row['Plastic Count'],
                        'name': contact_row['Name'],
                        'distance': distance,  # Distance in kilometers
                        'contact': contact_row['Contact'],
                        'Geo_tag_url': row['Geo Tag'],
                        }
            
            nearest_person_info.append(nearest_person)
        global df2
        df2= pd.DataFrame(nearest_person_info)
        #print(df2)

        
    

        self.load_button.setEnabled(True)
        self.next_button.setEnabled(True)
        self.process_image_button.setEnabled(True)
        self.generate_result_button.setEnabled(True)
        

        self.done_signal.emit()
        
        


    def close_loading_dialog(self):
        if self.loading_dialog:
            self.loading_dialog.accept() 


    def populate_processed_images(self):
        try:
            folder_path = "runs/detect/predict"
            images = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            num_columns = 4
            current_col = 0
            current_row = 0
            thumbnail_size = QSize(150, 150)  # Adjust thumbnail size as needed
            vertical_spacing = 4  # You can change this value to adjust the spacing
            self.process_screen_layout.setVerticalSpacing(vertical_spacing)
            for image in images:
                image_path = os.path.join(folder_path, image)
                pixmap = QPixmap(image_path).scaled(thumbnail_size, Qt.KeepAspectRatio)
                thumbnail_label = QLabel()
                thumbnail_label.setPixmap(pixmap)
                thumbnail_label.mousePressEvent = lambda event, path=image_path: self.open_image_display(path)
                self.process_screen_layout.addWidget(thumbnail_label, current_row, current_col, Qt.AlignTop)
                current_col += 1
                if current_col >= num_columns:
                    current_col = 0
                    current_row += 1

        except:
            pass

    def display_contact_csv(self, csv_path):
        if hasattr(self, 'contact_table'):
            self.contact_table.deleteLater()

        self.contact_table = QTableWidget(self.contact_screen_widget)
        self.contact_table.setStyleSheet("color: white; background-color: rgb(68, 70, 84);")
        header = self.contact_table.horizontalHeader()
        header.setStyleSheet("color: red; background-color: rgb(68, 70, 84);")
        data = pd.read_csv(csv_path)
        rows, cols = data.shape
        self.contact_table.setRowCount(rows)
        self.contact_table.setColumnCount(cols)
        self.contact_table.setHorizontalHeaderLabels(data.columns)
        for i in range(rows):
            for j in range(cols):
                item = QTableWidgetItem(str(data.iat[i, j]))
                item.setTextAlignment(Qt.AlignCenter)
                self.contact_table.setItem(i, j, item)
        self.contact_screen_layout.addWidget(self.contact_table)



    def populate_result_tab(self, table, dataframe):
        data = dataframe
        rows, cols = data.shape
        table.setRowCount(rows)
        table.setColumnCount(cols)
        table.setHorizontalHeaderLabels(data.columns)
        header = table.horizontalHeader()
        header.setStyleSheet("color: black; background-color: rgb(52, 54, 65);")
        for i in range(rows):
            for j in range(cols):
                item = QTableWidgetItem(str(data.iat[i, j]))
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(i, j, item)


    def show_generate_result(self):
        try:
            self.populate_result_tab(self.result1_table, df)  # Populate the first tab
            
            self.populate_result_tab(self.result2_table, df2)  # Populate the second tab
            plot_coordinates_on_map(df)
            self.map_view.load(QUrl.fromLocalFile(os.path.abspath("plastic_count_map.html")))
            self.stacked_widget.setCurrentIndex(4)
        except:
            self.stacked_widget.setCurrentIndex(4)
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setWindowTitle("Plastic Free River Solution")
    window.setGeometry(100, 100, 800, 600)
    window.show()
    sys.exit(app.exec_())
