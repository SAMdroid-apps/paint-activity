# -*- coding: utf-8 -*-

from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
import math

from sugar3.graphics import style
from sugar3.graphics.palette import ToolInvoker
from sugar3.graphics.colorbutton import _ColorButton
from sugar3.graphics.radiotoolbutton import RadioToolButton

# this strings are here only to enable pootle to translate them
# and do not broke the old versions
_old_strings = [_('Size: '), _('Opacity: '), _('Circle'), _('Square')]


class BrushButton(_ColorButton):
    """This is a ColorButton but show the color, the size and the shape
    of the brush.
    Instead of a color selector dialog it will pop up a Sugar palette.
    As a preview an DrawingArea is used, to use the same methods to
    draw than in the main window.
    """

    __gtype_name__ = 'BrushButton'

    def __init__(self, **kwargs):
        self._title = _('Choose brush properties')
        self._color = Gdk.Color(0, 0, 0)
        self._has_palette = True
        self._has_invoker = True
        self._palette = None
        self._accept_drag = True
        self._brush_size = 2
        self._stamp_size = 20
        self._brush_shape = 'circle'
        self._alpha = 1.0
        self._resized_stamp = None
        self._preview = Gtk.DrawingArea()
        self._preview.set_size_request(style.STANDARD_ICON_SIZE,
                                        style.STANDARD_ICON_SIZE)
        self._ctx = None

        GObject.GObject.__init__(self, **kwargs)
        self._preview.set_events(Gdk.EventMask.BUTTON_PRESS_MASK)

        self._preview.connect("draw", self.draw)
        self.set_image(self._preview)

        if self._has_palette and self._has_invoker:
            self._invoker = WidgetInvoker(self)
            # FIXME: This is a hack.
            self._invoker.has_rectangle_gap = lambda: False
            self._invoker.palette = self._palette

#    def _setup(self):
#        if self.get_window() is not None:
#            self._preview.show()
#            self.show_all()

    def get_brush_size(self):
        return self._brush_size

    def set_brush_size(self, brush_size):
        self._brush_size = brush_size
        self._preview.queue_draw()

    brush_size = GObject.property(type=int, getter=get_brush_size,
                    setter=set_brush_size)

    def get_brush_shape(self):
        return self._brush_shape

    def set_brush_shape(self, brush_shape):
        self._brush_shape = brush_shape
        self._preview.queue_draw()

    brush_shape = GObject.property(type=str, getter=get_brush_shape,
                    setter=set_brush_shape)

    def set_color(self, color):
        """
        @ param color Gdk.Color
        """
        self._color = color
        self._preview.queue_draw()

    def get_stamp_size(self):
        return self._stamp_size

    def set_stamp_size(self, stamp_size):
        self._stamp_size = stamp_size
        self._preview.queue_draw()

    stamp_size = GObject.property(type=int, getter=get_stamp_size,
                    setter=set_stamp_size)

    def set_resized_stamp(self, resized_stamp):
        self._resized_stamp = resized_stamp

    def stop_stamping(self):
        self._resized_stamp = None
        self._preview.queue_draw()

    def is_stamping(self):
        return self._resized_stamp != None

    def set_alpha(self, alpha):
        self._alpha = alpha
        self._preview.queue_draw()

    def draw(self, widget, ctx):
        #if self._ctx is None:
        #    self._setup()

        if self.get_window() is not None:
            center = style.STANDARD_ICON_SIZE / 2
            ctx.rectangle(0, 0, style.STANDARD_ICON_SIZE,
                    style.STANDARD_ICON_SIZE)
            ctx.set_source_rgb(1.0, 1.0, 1.0)
            ctx.fill()

            if self.is_stamping():
                width = self._resized_stamp.get_width()
                height = self._resized_stamp.get_height()
                dx = center - width / 2
                dy = center - height / 2

                ctx.rectangle(dx, dy, width, height)
                Gdk.cairo_set_source_pixbuf(ctx, self._resized_stamp, 0, 0)
                ctx.paint()

            else:
                red = float(self._color.red) / 65535.0
                green = float(self._color.green) / 65535.0
                blue = float(self._color.blue) / 65535.0
                ctx.set_source_rgba(red, green, blue, self._alpha)
                if self._brush_shape == 'circle':
                    ctx.arc(center, center, self._brush_size / 2, 0.,
                            2 * math.pi)
                    ctx.fill()

                elif self._brush_shape == 'square':
                    ctx.rectangle(center - self._brush_size / 2,
                            center - self._brush_size / 2, self._brush_size,
                            self._brush_size)
                    ctx.fill()

        return False

    def do_style_set(self, previous_style):
        pass

    def set_icon_name(self, icon_name):
        pass

    def get_icon_name(self):
        pass

    def set_icon_size(self, icon_size):
        pass

    def get_icon_size(self):
        pass


class ButtonStrokeColor(Gtk.ToolItem):
    """Class to manage the Stroke Color of a Button"""

    __gtype_name__ = 'BrushColorToolButton'
    __gsignals__ = {'color-set': (GObject.SignalFlags.RUN_FIRST, None,
        tuple())}

    def __init__(self, activity, **kwargs):
        self._activity = activity
        self.properties = self._activity.area.tool
        self._accelerator = None
        self._tooltip = None
        self._palette_invoker = ToolInvoker()
        self._palette = None

        GObject.GObject.__init__(self, **kwargs)

        # The Gtk.ToolButton has already added a normal button.
        # Replace it with a ColorButton
        self.color_button = BrushButton(has_invoker=False)
        self.add(self.color_button)
        self.color_button.set_brush_size(2)
        self.color_button.set_brush_shape('circle')
        self.color_button.set_stamp_size(20)

        # The following is so that the behaviour on the toolbar is correct.
        self.color_button.set_relief(Gtk.ReliefStyle.NONE)

        self._palette_invoker.attach_tool(self)
        self._palette_invoker.props.toggle_palette = True
        self._palette_invoker.props.lock_palette = True

        # This widget just proxies the following properties to the colorbutton
        self.color_button.connect('notify::color', self.__notify_change)
        self.color_button.connect('notify::icon-name', self.__notify_change)
        self.color_button.connect('notify::icon-size', self.__notify_change)
        self.color_button.connect('notify::title', self.__notify_change)
        self.color_button.connect('can-activate-accel',
                             self.__button_can_activate_accel_cb)

        self.create_palette()

    def __button_can_activate_accel_cb(self, button, signal_id):
        # Accept activation via accelerators regardless of this widget's state
        return True

    def __notify_change(self, widget, pspec):
        #new_color = self.alloc_color(self.get_color())
        #self.color_button.set_color(new_color)
        self.color_button.set_color(self.get_color())
        self.notify(pspec.name)

    def _color_button_cb(self, widget, pspec):
        color = self.get_color()
        self.set_stroke_color(color)

#    def alloc_color(self, color):
#        colormap = self._activity.area.get_colormap()
#        return colormap.alloc_color(color.red, color.green, color.blue)

    def create_palette(self):
        self._palette = self.get_child().create_palette()

        color_palette_hbox = self._palette._picker_hbox
        content_box = Gtk.VBox()

        self.vbox_brush_options = Gtk.VBox()

        # This is where we set restrictions for size:
        # Initial value, minimum value, maximum value, step
        adj = Gtk.Adjustment(self.properties['line size'], 1.0, 100.0, 1.0)
        self.size_scale = Gtk.HScale()
        self.size_scale.set_adjustment(adj)
        self.size_scale.set_draw_value(False)
        self.size_scale.set_size_request(style.zoom(200), -1)
        label = Gtk.Label(label=_('Size'))
        label.props.halign = Gtk.Align.START
        self.vbox_brush_options.pack_start(label, True, True, 0)
        self.vbox_brush_options.pack_start(self.size_scale, True, True, 0)

        self.size_scale.connect('value-changed', self._on_value_changed)

        # Control alpha
        alpha = self.properties['alpha'] * 100
        adj_alpha = Gtk.Adjustment(alpha, 10.0, 100.0, 1.0)
        self.alpha_scale = Gtk.HScale()
        self.alpha_scale.set_adjustment(adj_alpha)
        self.alpha_scale.set_draw_value(False)
        self.alpha_scale.set_size_request(style.zoom(200), -1)
        self.alpha_label = Gtk.Label(label=_('Opacity'))
        self.alpha_label.props.halign = Gtk.Align.START
        self.vbox_brush_options.pack_start(self.alpha_label, True, True, 0)
        self.vbox_brush_options.pack_start(self.alpha_scale, True, True, 0)

        self.alpha_scale.connect('value-changed', self._on_alpha_changed)

        # User is able to choose Shapes for 'Brush' and 'Eraser'
        shape_box = Gtk.HBox()
        content_box.pack_start(self.vbox_brush_options, True, True, 0)
        item1 = RadioToolButton()
        item1.set_icon_name('tool-shape-ellipse')
        item1.set_active(True)

        item2 = RadioToolButton()
        item2.set_icon_name('tool-shape-rectangle')
        item2.props.group = item1

        item1.connect('toggled', self._on_toggled, self.properties, 'circle')
        item2.connect('toggled', self._on_toggled, self.properties, 'square')

        shape_box.pack_start(Gtk.Label(_('Shape')), True, True, 0)
        shape_box.pack_start(item1, True, True, 0)
        shape_box.pack_start(item2, True, True, 0)

        self.vbox_brush_options.pack_start(shape_box, True, True, 0)

        keep_aspect_checkbutton = Gtk.CheckButton(_('Keep aspect'))
        ratio = self._activity.area.keep_aspect_ratio
        keep_aspect_checkbutton.set_active(ratio)
        keep_aspect_checkbutton.connect('toggled',
            self._keep_aspect_checkbutton_toggled)
        self.vbox_brush_options.pack_start(keep_aspect_checkbutton, True, True,
                0)

        color_palette_hbox.pack_start(Gtk.VSeparator(), True, True,
                                     padding=style.DEFAULT_SPACING)
        color_palette_hbox.pack_start(content_box, True, True, 10)
        color_palette_hbox.show_all()
        self._update_palette()
        return self._palette

    def _keep_aspect_checkbutton_toggled(self, checkbutton):
        self._activity.area.keep_aspect_ratio = checkbutton.get_active()

    def _update_palette(self):
        palette_children = self._palette._picker_hbox.get_children()
        if self.color_button.is_stamping():
            # Hide palette color widgets:
            for ch in palette_children[:4]:
                ch.hide()
            # Hide brush options:
            self.vbox_brush_options.hide()
            self.alpha_label.hide()
            self.alpha_scale.hide()
            # Change title:
            self.set_title(_('Stamp properties'))
        else:
            # Show palette color widgets:
            for ch in palette_children[:4]:
                ch.show_all()
            # Show brush options:
            self.vbox_brush_options.show_all()
            self.alpha_label.show()
            self.alpha_scale.show()
            # Change title:
            self.set_title(_('Brush properties'))

        self._palette._picker_hbox.resize_children()
        self._palette._picker_hbox.queue_draw()

    def update_stamping(self):
        if self.color_button.is_stamping():
            self.size_scale.set_value(self.color_button.stamp_size)
        else:
            self.size_scale.set_value(self.color_button.brush_size)
        self._update_palette()

    def _on_alpha_changed(self, scale):
        alpha = scale.get_value() / 100.0
        self._activity.area.set_alpha(alpha)
        self.color_button.set_alpha(alpha)

    def _on_value_changed(self, scale):
        size = int(scale.get_value())
        if self.color_button.is_stamping():
            self.properties['stamp size'] = size
            resized_stamp = self._activity.area.resize_stamp(size)
            self.color_button.set_resized_stamp(resized_stamp)
            self.color_button.set_stamp_size(self.properties['stamp size'])
        else:
            self.properties['line size'] = size
            self.color_button.set_brush_size(self.properties['line size'])
        self._activity.area.set_tool(self.properties)

    def _on_toggled(self, radiobutton, tool, shape):
        if radiobutton.get_active():
            self.properties['line shape'] = shape
            self.color_button.set_brush_shape(shape)
            self.color_button.set_brush_size(self.properties['line size'])

    def get_palette_invoker(self):
        return self._palette_invoker

    def set_palette_invoker(self, palette_invoker):
        self._palette_invoker.detach()
        self._palette_invoker = palette_invoker

    palette_invoker = GObject.property(
        type=object, setter=set_palette_invoker, getter=get_palette_invoker)

    def set_color(self, color):
        self.color_button.set_color(color)

    def get_color(self):
        return self.get_child().props.color

    color = GObject.property(type=object, getter=get_color, setter=set_color)

    def set_title(self, title):
        self.get_child().props.title = title

    def get_title(self):
        return self.get_child().props.title

    title = GObject.property(type=str, getter=get_title, setter=set_title)

    def do_expose_event(self, event):
        child = self.get_child()
        allocation = self.get_allocation()
        if self._palette and self._palette.is_up():
            invoker = self._palette.props.invoker
            invoker.draw_rectangle(event, self._palette)
        elif child.state == Gtk.StateType.PRELIGHT:
            child.style.paint_box(event.window, Gtk.StateType.PRELIGHT,
                                  Gtk.ShadowType.NONE, event.area,
                                  child, 'toolbutton-prelight',
                                  allocation.x, allocation.y,
                                  allocation.width, allocation.height)

        Gtk.ToolButton.do_expose_event(self, event)
