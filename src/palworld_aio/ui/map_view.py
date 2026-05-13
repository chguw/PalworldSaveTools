from PySide6.QtWidgets import QGraphicsView, QLabel
from PySide6.QtCore import Qt, QPointF, QPoint, Signal, QTimer
from PySide6.QtGui import QPainter
from i18n import t
import palworld_coord
from .map_markers import BaseMarker, PlayerMarker
from .map_items import ExclusionZoneItem, PolygonExclusionZoneItem, ZonePreviewItem, PolygonPreviewItem
class MapGraphicsView(QGraphicsView):
    marker_clicked = Signal(object, object)
    marker_double_clicked = Signal(object, object)
    marker_right_clicked = Signal(object, QPointF)
    empty_space_right_clicked = Signal(QPointF)
    marker_hover_entered = Signal(object, QPointF)
    marker_hover_left = Signal()
    zone_right_clicked = Signal(object, QPointF)
    zone_double_clicked = Signal(object)
    zone_point_a_set = Signal(QPointF)
    zone_created = Signal(QPointF, QPointF)
    zone_drawing_cancelled = Signal()
    polygon_point_added = Signal(QPointF)
    polygon_closed = Signal(list)
    zoom_changed = Signal(float)
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setBackgroundBrush(Qt.transparent)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMouseTracking(True)
        self._hovered_marker = None
        self.zone_drawing_mode = False
        self.zone_shape_type = 'rect'
        self.zone_point_a = None
        self.zone_preview_item = None
        self.polygon_preview_item = None
        self.polygon_points = []
        zoom_config = self.config['zoom']
        self.zoom_factor = zoom_config['factor']
        self.current_zoom = 1.0
        self.min_zoom = zoom_config['min']
        self.max_zoom = zoom_config['max']
        self.zoom_timer = QTimer()
        self.zoom_timer.timeout.connect(self._smooth_zoom_step)
        self.target_zoom = 1.0
        self.target_center = None
        self.is_animating = False
        self.base_scale = 1.0
        self.coords_label = QLabel(f"{(t('cursor_coords') if t else 'Cursor')}: 0,0", self)
        self.coords_label.setStyleSheet('background-color: rgba(0,0,0,150); color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; min-width: 120px;')
        self.coords_label.move(10, self.height() - 30)
        self.coords_label.setVisible(True)
        self.coords_label.setAttribute(Qt.WA_ShowWithoutActivating)
        self.zoom_label = QLabel((t('zoom') if t else 'Zoom') + ': 100%', self)
        self.zoom_label.setStyleSheet('background-color: rgba(0,0,0,150); color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; min-width: 80px;')
        self.zoom_label.move(self.width() - 100, self.height() - 30)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setAttribute(Qt.WA_ShowWithoutActivating)
        self.overlay_position_callback = None
    def animate_to_coords(self, x, y, zoom_level=None):
        if zoom_level is None:
            zoom_level = self.config['zoom']['double_click_target']
        self.target_zoom = zoom_level
        self.target_center = QPointF(x, y)
        self.resetTransform()
        self.scale(self.base_scale, self.base_scale)
        self.current_zoom = 1.0
        self.centerOn(self.target_center)
        self.is_animating = True
        fps = self.config['zoom']['animation_fps']
        interval = int(1000 / fps)
        if not self.zoom_timer.isActive():
            self.zoom_timer.start(interval)
    def _clamp_center_to_bounds(self, center_point):
        if not self.scene():
            return center_point
        scene_rect = self.scene().sceneRect()
        if scene_rect.isEmpty():
            return center_point
        viewport_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        min_x = scene_rect.left() + viewport_rect.width() / 2
        max_x = scene_rect.right() - viewport_rect.width() / 2
        min_y = scene_rect.top() + viewport_rect.height() / 2
        max_y = scene_rect.bottom() - viewport_rect.height() / 2
        if min_x > max_x:
            min_x = max_x = scene_rect.center().x()
        if min_y > max_y:
            min_y = max_y = scene_rect.center().y()
        x = max(min_x, min(center_point.x(), max_x))
        y = max(min_y, min(center_point.y(), max_y))
        return QPointF(x, y)
    def wheelEvent(self, event):
        zoom_in = event.angleDelta().y() > 0
        if zoom_in:
            factor = self.zoom_factor
            self.current_zoom *= factor
        else:
            factor = 1 / self.zoom_factor
            self.current_zoom *= factor
        if self.current_zoom < self.min_zoom:
            factor = self.min_zoom / (self.current_zoom / factor)
            self.current_zoom = self.min_zoom
        elif self.current_zoom > self.max_zoom:
            factor = self.max_zoom / (self.current_zoom / factor)
            self.current_zoom = self.max_zoom
        self.scale(factor, factor)
        self.zoom_label.setText((t('zoom') if t else 'Zoom') + f': {int(self.current_zoom * 100)}%')
        self.zoom_changed.emit(self.current_zoom)
    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, BaseMarker):
            if event.button() == Qt.LeftButton:
                self.scene().clearSelection()
                item.setSelected(True)
                item.start_glow()
                self.marker_clicked.emit(item.base_data, item)
            elif event.button() == Qt.RightButton:
                self.marker_right_clicked.emit(item.base_data, event.globalPosition())
                return
        elif isinstance(item, PlayerMarker):
            if event.button() == Qt.LeftButton:
                self.scene().clearSelection()
                item.setSelected(True)
                item.start_glow()
                self.marker_clicked.emit(item.player_data, item)
            elif event.button() == Qt.RightButton:
                self.marker_right_clicked.emit(item.player_data, event.globalPosition())
                return
        elif isinstance(item, (ExclusionZoneItem, PolygonExclusionZoneItem)):
            if event.button() == Qt.RightButton:
                self.zone_right_clicked.emit(item, event.globalPosition())
                return
        elif event.button() == Qt.RightButton:
            self.empty_space_right_clicked.emit(event.globalPosition())
            return
        elif event.button() == Qt.LeftButton:
            if self.zone_drawing_mode and self.zone_shape_type == 'polygon' and self.polygon_preview_item:
                scene_pos = self.mapToScene(event.pos())
                self.polygon_points.append(scene_pos)
                self.polygon_point_added.emit(scene_pos)
                self.polygon_preview_item.add_point(scene_pos)
                return
            self.scene().clearSelection()
        super().mousePressEvent(event)
    def mouseDoubleClickEvent(self, event):
        if self.zone_drawing_mode and event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            if self.zone_shape_type == 'rect':
                if self.zone_point_a is None:
                    self.zone_point_a = scene_pos
                    self.zone_point_a_set.emit(scene_pos)
                    if self.scene():
                        self.zone_preview_item = ZonePreviewItem()
                        self.scene().addItem(self.zone_preview_item)
                else:
                    point_b = scene_pos
                    self.zone_created.emit(self.zone_point_a, point_b)
                    self._clear_zone_preview()
                    if self.scene():
                        self.zone_preview_item = ZonePreviewItem()
                        self.scene().addItem(self.zone_preview_item)
            elif not self.polygon_points:
                self.polygon_points.append(scene_pos)
                self.polygon_point_added.emit(scene_pos)
                if self.scene():
                    self.polygon_preview_item = PolygonPreviewItem()
                    self.scene().addItem(self.polygon_preview_item)
                    self.polygon_preview_item.add_point(scene_pos)
            elif len(self.polygon_points) >= 3:
                self.polygon_closed.emit(self.polygon_points)
                self._clear_polygon_preview()
            return
        item = self.itemAt(event.pos())
        if isinstance(item, BaseMarker):
            if event.button() == Qt.LeftButton:
                self.marker_double_clicked.emit(item.base_data, item)
                zoom_level = self.config['zoom']['double_click_target']
                self.animate_to_marker(item, zoom_level=zoom_level, duration_ms=1500)
                return
        elif isinstance(item, PlayerMarker):
            if event.button() == Qt.LeftButton:
                self.marker_double_clicked.emit(item.player_data, item)
                zoom_level = self.config['zoom']['double_click_target']
                self.animate_to_marker(item, zoom_level=zoom_level, duration_ms=1500)
                return
        elif isinstance(item, (ExclusionZoneItem, PolygonExclusionZoneItem)):
            if event.button() == Qt.LeftButton:
                self.zone_double_clicked.emit(item)
                return
        super().mouseDoubleClickEvent(event)
    def mouseMoveEvent(self, event):
        if self.zone_drawing_mode:
            scene_pos = self.mapToScene(event.pos())
            if self.zone_shape_type == 'rect':
                self._update_zone_preview(scene_pos)
            elif self.zone_shape_type == 'polygon' and self.polygon_preview_item:
                self.polygon_preview_item.set_preview_point(scene_pos)
            if self.scene() and self.scene().sceneRect().contains(scene_pos):
                rect = self.scene().sceneRect()
                width, height = (rect.width(), rect.height())
                img_x, img_y = (scene_pos.x(), scene_pos.y())
                x_world = img_x / width * 2000 - 1000
                y_world = 1000 - img_y / height * 2000
                save_x, save_y = palworld_coord.map_to_sav(x_world, y_world, new=True)
                old_x, old_y = palworld_coord.sav_to_map(save_x, save_y, new=False)
                self.coords_label.setText(f"{(t('cursor_coords') if t else 'Cursor')}: {int(old_x)},{int(old_y)}")
            super().mouseMoveEvent(event)
            return
        item = self.itemAt(event.pos())
        if isinstance(item, BaseMarker):
            if self._hovered_marker != item:
                if self._hovered_marker is not None:
                    self.marker_hover_left.emit()
                self._hovered_marker = item
                global_pos = self.mapToGlobal(event.pos())
                self.marker_hover_entered.emit(item.base_data, QPointF(global_pos.x(), global_pos.y()))
        elif isinstance(item, PlayerMarker):
            if self._hovered_marker != item:
                if self._hovered_marker is not None:
                    self.marker_hover_left.emit()
                self._hovered_marker = item
                global_pos = self.mapToGlobal(event.pos())
                self.marker_hover_entered.emit(item.player_data, QPointF(global_pos.x(), global_pos.y()))
        elif self._hovered_marker is not None:
            self._hovered_marker = None
            self.marker_hover_left.emit()
        scene_pos = self.mapToScene(event.pos())
        if self.scene() and self.scene().sceneRect().contains(scene_pos):
            rect = self.scene().sceneRect()
            width, height = (rect.width(), rect.height())
            img_x, img_y = (scene_pos.x(), scene_pos.y())
            x_world = img_x / width * 2000 - 1000
            y_world = 1000 - img_y / height * 2000
            save_x, save_y = palworld_coord.map_to_sav(x_world, y_world, new=True)
            old_x, old_y = palworld_coord.sav_to_map(save_x, save_y, new=False)
            self.coords_label.setText(f"{(t('cursor_coords') if t else 'Cursor')}: {int(old_x)},{int(old_y)}")
        super().mouseMoveEvent(event)
    def keyPressEvent(self, event):
        if self.zone_drawing_mode and event.key() == Qt.Key_Escape:
            self.zone_drawing_cancelled.emit()
        super().keyPressEvent(event)
    def leaveEvent(self, event):
        if self._hovered_marker is not None:
            self._hovered_marker = None
            self.marker_hover_left.emit()
        super().leaveEvent(event)
    def animate_to_marker(self, marker, zoom_level=None, duration_ms=1500):
        if zoom_level is None:
            zoom_level = self.config['zoom']['double_click_target']
        zoom_level = max(self.min_zoom, min(zoom_level, self.max_zoom))
        view_center = self.mapToScene(self.viewport().rect().center())
        self.start_center = QPointF(view_center.x(), view_center.y())
        target_pos = QPointF(marker.center_x, marker.center_y)
        self.target_center = target_pos
        self.target_zoom = zoom_level
        self.is_animating = True
        fps = self.config['zoom']['animation_fps']
        interval = int(1000 / fps)
        zoom_diff = abs(zoom_level - self.current_zoom)
        adaptive_duration = max(100, min(int(zoom_diff * 100), duration_ms))
        steps = max(1, int(adaptive_duration / interval))
        self._animation_steps = steps
        self._current_step = 0
        if not self.zoom_timer.isActive():
            self.zoom_timer.start(interval)
    def _smooth_zoom_step(self):
        if not self.is_animating:
            self.zoom_timer.stop()
            return
        zoom_diff = self.target_zoom - self.current_zoom
        if abs(zoom_diff) < 0.05:
            factor = self.target_zoom / self.current_zoom
            self.scale(factor, factor)
            self.current_zoom = self.target_zoom
            clamped_center = self._clamp_center_to_bounds(self.target_center)
            self.centerOn(clamped_center)
            self.is_animating = False
            self.zoom_timer.stop()
            self.zoom_label.setText((t('zoom') if t else 'Zoom') + f': {int(self.current_zoom * 100)}%')
            self.zoom_changed.emit(self.current_zoom)
            self._validate_and_recover_view()
            return
        if hasattr(self, '_animation_steps'):
            self._current_step += 1
            progress = self._current_step / self._animation_steps
            eased_progress = 1 - (1 - progress) ** 3
            target_zoom_for_step = self.current_zoom + (self.target_zoom - self.current_zoom) * eased_progress
            factor = target_zoom_for_step / self.current_zoom if self.current_zoom > 0 else 1
            self.current_zoom = target_zoom_for_step
            self.scale(factor, factor)
            if hasattr(self, 'start_center') and hasattr(self, 'target_center'):
                interpolated_x = self.start_center.x() + (self.target_center.x() - self.start_center.x()) * eased_progress
                interpolated_y = self.start_center.y() + (self.target_center.y() - self.start_center.y()) * eased_progress
                interpolated_center = QPointF(interpolated_x, interpolated_y)
                clamped_center = self._clamp_center_to_bounds(interpolated_center)
                self.centerOn(clamped_center)
            self.zoom_label.setText((t('zoom') if t else 'Zoom') + f': {int(self.current_zoom * 100)}%')
            self.zoom_changed.emit(self.current_zoom)
        else:
            easing_factor = self.config['zoom']['animation_speed']
            zoom_step = zoom_diff * easing_factor
            factor = (self.current_zoom + zoom_step) / self.current_zoom
            self.current_zoom += zoom_step
            self.scale(factor, factor)
            self.zoom_label.setText((t('zoom') if t else 'Zoom') + f': {int(self.current_zoom * 100)}%')
            self.zoom_changed.emit(self.current_zoom)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.coords_label.move(10, self.height() - 30)
        self.zoom_label.move(self.width() - 100, self.height() - 30)
        self.coords_label.raise_()
        self.zoom_label.raise_()
        if self.overlay_position_callback:
            self.overlay_position_callback()
    def reset_view(self):
        self.resetTransform()
        self.current_zoom = 1.0
        if self.scene():
            rect = self.scene().sceneRect()
            if rect.width() > 0 and rect.height() > 0:
                viewport = self.viewport()
                scale_x = viewport.width() / rect.width()
                scale_y = viewport.height() / rect.height()
                scale = max(scale_x, scale_y)
                self.base_scale = scale
                self.scale(scale, scale)
        self.zoom_changed.emit(self.current_zoom)
    def _validate_and_recover_view(self):
        if not self.scene():
            return
        scene_rect = self.scene().sceneRect()
        viewport_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        if not viewport_rect.intersects(scene_rect):
            self.reset_view()
            return True
        return False
    def set_zone_drawing_mode(self, enabled):
        self.zone_drawing_mode = enabled
        if not enabled:
            self._clear_zone_preview()
            self._clear_polygon_preview()
    def get_zone_drawing_mode(self):
        return self.zone_drawing_mode
    def set_zone_shape_type(self, shape_type):
        self.zone_shape_type = shape_type
        if shape_type == 'polygon':
            self._clear_zone_preview()
        else:
            self._clear_polygon_preview()
    def get_zone_shape_type(self):
        return self.zone_shape_type
    def _clear_zone_preview(self):
        if self.zone_preview_item:
            if self.scene():
                self.scene().removeItem(self.zone_preview_item)
            self.zone_preview_item = None
        self.zone_point_a = None
    def _clear_polygon_preview(self):
        if self.polygon_preview_item:
            if self.scene():
                self.scene().removeItem(self.polygon_preview_item)
            self.polygon_preview_item = None
        self.polygon_points = []
    def _update_zone_preview(self, current_point):
        if self.zone_preview_item and self.zone_point_a:
            self.zone_preview_item.update_preview(self.zone_point_a, current_point)