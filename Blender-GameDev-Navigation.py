bl_info = {
    'name': 'GameDev Navigation',
    'author': 'FAAATQ',
    'version': (0, 3, 0),
    'blender': (4, 0, 0),
    'location': 'Edit > Preferences > Add-ons > GameDev Navigation',
    'description': 'Unity- and Unreal-style RMB viewport navigation for Blender',
    'category': '3D View',
}

import bpy
import blf
import gpu
import json
import time
from pathlib import Path
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Quaternion
from bpy.props import (
    BoolProperty,
    FloatProperty,
    StringProperty,
)
from bpy.types import AddonPreferences, Operator

REGISTERED_KEYMAP_ITEMS = []
DRAW_HANDLES = set()

DEFAULT_NAV_TRIGGER = 'RIGHTMOUSE'
DEFAULT_CURSOR_TRIGGER = 'RIGHTMOUSE'
DEFAULT_CURSOR_MOD_SHIFT = True
ADDON_ID = __package__ or __name__
TRANSLATION_ID = f'{ADDON_ID}.translations'

LOCALES_DIR = Path(__file__).resolve().parent / 'locales'


def load_translations():
    translations = {}
    if not LOCALES_DIR.is_dir():
        log(f'No locales directory found at {LOCALES_DIR}')
        return translations

    for locale_path in sorted(LOCALES_DIR.glob('*.json')):
        if locale_path.name.startswith('_'):
            continue
        try:
            data = json.loads(locale_path.read_text(encoding='utf-8'))
            locale = data['locale']
            aliases = data.get('aliases', [])
            messages = data['messages']
            if not isinstance(locale, str) or not isinstance(aliases, list) or not isinstance(messages, dict):
                raise TypeError('locale, aliases, or messages has an invalid type')

            catalog = {}
            for source, translated in messages.items():
                if not isinstance(source, str) or not isinstance(translated, str) or not translated:
                    continue
                catalog[('*', source)] = translated
                catalog[('Operator', source)] = translated
            for locale_id in (locale, *aliases):
                if not isinstance(locale_id, str) or not locale_id:
                    raise TypeError('locale identifiers must be non-empty strings')
                translations.setdefault(locale_id, {}).update(catalog)
            log(f'Loaded locale {locale} from {locale_path.name}')
        except (OSError, KeyError, TypeError, ValueError) as error:
            log(f'SKIP locale {locale_path.name} | {error}')

    return translations


def update_keymap_preferences(_self, context):
    rebuild_keymaps(context)


def log(msg):
    print('[GameDevNavAddon]', msg)


def set_font_size(font_id, size):
    try:
        blf.size(font_id, size)
    except TypeError:
        blf.size(font_id, size, 72)


class UnityNavPreferences(AddonPreferences):
    bl_idname = ADDON_ID

    enabled: BoolProperty(
        name='Enable GameDev Navigation',
        description='Register Unity- and Unreal-style navigation key bindings',
        default=True,
        update=update_keymap_preferences,
    )
    mouse_sensitivity: FloatProperty(
        name='Mouse Sensitivity',
        default=0.0032,
        min=0.0001,
        max=0.02,
        soft_min=0.001,
        soft_max=0.01,
        precision=4,
    )
    acceleration: FloatProperty(
        name='Acceleration',
        default=20.0,
        min=1.0,
        max=100.0,
        soft_min=5.0,
        soft_max=40.0,
    )
    damping: FloatProperty(
        name='Damping',
        default=10.0,
        min=0.1,
        max=50.0,
        soft_min=2.0,
        soft_max=20.0,
    )
    max_speed: FloatProperty(
        name='Max Speed',
        default=8.0,
        min=0.1,
        max=100.0,
        soft_min=1.0,
        soft_max=25.0,
    )
    boost_multiplier: FloatProperty(
        name='Boost Multiplier',
        default=3.0,
        min=1.0,
        max=20.0,
        soft_min=1.5,
        soft_max=8.0,
    )
    timer_step: FloatProperty(
        name='Timer Step',
        default=0.01,
        min=0.001,
        max=0.1,
        soft_min=0.005,
        soft_max=0.03,
        precision=4,
    )
    scroll_speed_step: FloatProperty(
        name='Scroll Speed Step',
        default=1.15,
        min=1.01,
        max=2.0,
        soft_min=1.05,
        soft_max=1.4,
        precision=2,
    )
    min_speed_scale: FloatProperty(
        name='Min Speed Scale',
        default=0.2,
        min=0.01,
        max=2.0,
        soft_min=0.05,
        soft_max=1.0,
        precision=2,
    )
    max_speed_scale: FloatProperty(
        name='Max Speed Scale',
        default=8.0,
        min=1.0,
        max=50.0,
        soft_min=2.0,
        soft_max=20.0,
        precision=2,
    )
    overlay_duration: FloatProperty(
        name='Overlay Duration',
        default=1.0,
        min=0.1,
        max=5.0,
        soft_min=0.3,
        soft_max=2.0,
        precision=2,
    )
    overlay_width: FloatProperty(
        name='Overlay Width',
        default=260.0,
        min=120.0,
        max=800.0,
        soft_min=180.0,
        soft_max=400.0,
    )
    overlay_height: FloatProperty(
        name='Overlay Height',
        default=54.0,
        min=24.0,
        max=200.0,
        soft_min=36.0,
        soft_max=100.0,
    )
    nav_trigger: StringProperty(
        name='Navigation Trigger',
        description='Fallback Blender event type used to start and stop navigation',
        default=DEFAULT_NAV_TRIGGER,
        update=update_keymap_preferences,
    )
    enable_cursor_shortcut: BoolProperty(
        name='Enable 3D Cursor Shortcut',
        description='Register Shift + Cursor Trigger for Blender users who need 3D Cursor placement; disabled by default to avoid conflicting with navigation boost',
        default=False,
        update=update_keymap_preferences,
    )
    cursor_trigger: StringProperty(
        name='Cursor Trigger',
        description='Blender event type used with Shift to place the 3D Cursor',
        default=DEFAULT_CURSOR_TRIGGER,
        update=update_keymap_preferences,
    )

    def draw(self, _context):
        layout = self.layout

        layout.prop(self, 'enabled')

        navigation = layout.box()
        navigation.label(text='Navigation')
        navigation.enabled = self.enabled
        navigation.prop(self, 'mouse_sensitivity')
        navigation.prop(self, 'acceleration')
        navigation.prop(self, 'damping')
        navigation.prop(self, 'max_speed')
        navigation.prop(self, 'boost_multiplier')
        navigation.prop(self, 'timer_step')

        overlay = layout.box()
        overlay.label(text='Speed Overlay')
        overlay.enabled = self.enabled
        overlay.prop(self, 'scroll_speed_step')
        overlay.prop(self, 'min_speed_scale')
        overlay.prop(self, 'max_speed_scale')
        overlay.prop(self, 'overlay_duration')
        overlay.prop(self, 'overlay_width')
        overlay.prop(self, 'overlay_height')

        bindings = layout.box()
        bindings.label(text='Bindings')
        bindings.enabled = self.enabled
        km, kmi, kc = find_navigation_keymap_item(_context)
        if km and kmi and kc:
            try:
                from bl_ui import rna_keymap_ui
                rna_keymap_ui.draw_kmi([], kc, km, kmi, bindings, 0)
                bindings.operator('unity_nav.apply_binding', icon='FILE_REFRESH')
            except (ImportError, RuntimeError, TypeError, AttributeError):
                bindings.label(text='Native keymap editor unavailable')
        else:
            bindings.label(text='Keymap is initializing')
        bindings.prop(self, 'enable_cursor_shortcut')
        cursor = bindings.column()
        cursor.enabled = self.enable_cursor_shortcut
        cursor.prop(self, 'cursor_trigger')
        cursor.label(text='Cursor placement uses Shift + Cursor Trigger')

        status = 'Active' if self.enabled and REGISTERED_KEYMAP_ITEMS else 'Inactive'
        layout.label(text=f'Keymap Status: {status}')
        layout.operator('unity_nav.rebuild_keymap', icon='FILE_REFRESH')


def get_preferences(context=None):
    context = context or bpy.context
    preferences = getattr(context, 'preferences', None)
    if preferences is None:
        return None
    addon = preferences.addons.get(ADDON_ID)
    return addon.preferences if addon else None


class VIEW3D_OT_unity_nav(Operator):
    bl_idname = 'view3d.unity_nav'
    bl_label = 'GameDev View Navigation'
    bl_options = {'REGISTER', 'BLOCKING'}

    def _settings(self, context):
        return get_preferences(context)

    def _reset_state(self):
        self._timer = None
        self._pressed = set()
        self._velocity = Vector((0.0, 0.0, 0.0))
        self._region = None
        self._rv3d = None
        self._window = None
        self._area = None
        self._last_mouse_x = 0
        self._last_mouse_y = 0
        self._released = False
        self._speed_scale = 1.0
        self._overlay_until = 0.0
        self._draw_handle = None
        self._nav_trigger = DEFAULT_NAV_TRIGGER

    def _capture_context(self, context):
        self._area = context.area
        self._region = context.region
        self._rv3d = context.region_data
        self._window = context.window
        return bool(self._area and self._region and self._rv3d and self._window)

    def _get_eye_position(self):
        return self._rv3d.view_location + (self._rv3d.view_rotation @ Vector((0.0, 0.0, self._rv3d.view_distance)))

    def _enter_fps_view(self):
        eye_position = self._get_eye_position()
        self._rv3d.view_location = eye_position
        self._rv3d.view_distance = 0.0

    def _get_basis(self):
        rotation = self._rv3d.view_rotation
        forward = rotation @ Vector((0.0, 0.0, -1.0))
        right = rotation @ Vector((1.0, 0.0, 0.0))
        up = rotation @ Vector((0.0, 1.0, 0.0))
        return forward, right, up

    def _show_overlay(self, context):
        self._overlay_until = time.monotonic() + self._settings(context).overlay_duration

    def _draw_rect(self, x, y, w, h, color):
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        vertices = ((x, y), (x + w, y), (x + w, y + h), (x, y + h))
        batch = batch_for_shader(shader, 'TRI_FAN', {'pos': vertices})
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color)
        batch.draw(shader)
        gpu.state.blend_set('NONE')

    def _draw_overlay(self, context):
        if not self._area or not self._region:
            return

        settings = self._settings(context)
        remaining = self._overlay_until - time.monotonic()
        if remaining <= 0.0:
            return

        alpha = min(1.0, remaining / max(0.001, settings.overlay_duration))
        width = settings.overlay_width
        height = settings.overlay_height
        x = (self._region.width - width) * 0.5
        y = (self._region.height - height) * 0.5

        self._draw_rect(x, y, width, height, (0.22, 0.22, 0.24, 0.78 * alpha))

        text = f'{self._speed_scale:.2f}x'
        subtitle = bpy.app.translations.pgettext_iface('Navigation Speed')
        font_id = 0

        set_font_size(font_id, 22)
        text_width, _ = blf.dimensions(font_id, text)
        text_x = x + (width - text_width) * 0.5
        text_y = y + 16

        blf.color(font_id, 0.0, 0.0, 0.0, 0.45 * alpha)
        blf.position(font_id, text_x + 1, text_y - 1, 0)
        blf.draw(font_id, text)

        blf.color(font_id, 1.0, 1.0, 1.0, alpha)
        blf.position(font_id, text_x, text_y, 0)
        blf.draw(font_id, text)

        set_font_size(font_id, 12)
        sub_width, _ = blf.dimensions(font_id, subtitle)
        sub_x = x + (width - sub_width) * 0.5
        sub_y = y + height - 20

        blf.color(font_id, 0.0, 0.0, 0.0, 0.35 * alpha)
        blf.position(font_id, sub_x + 1, sub_y - 1, 0)
        blf.draw(font_id, subtitle)

        blf.color(font_id, 0.92, 0.92, 0.94, alpha)
        blf.position(font_id, sub_x, sub_y, 0)
        blf.draw(font_id, subtitle)

    def _draw_overlay_callback(self, context):
        self._draw_overlay(context)

    def _set_speed_scale(self, context, factor):
        settings = self._settings(context)
        self._speed_scale *= factor
        self._speed_scale = max(settings.min_speed_scale, min(settings.max_speed_scale, self._speed_scale))
        self._show_overlay(context)
        if self._area:
            self._area.tag_redraw()

    def _target_direction(self):
        forward, right, up = self._get_basis()
        direction = Vector((0.0, 0.0, 0.0))

        if 'W' in self._pressed:
            direction += forward
        if 'S' in self._pressed:
            direction -= forward
        if 'D' in self._pressed:
            direction += right
        if 'A' in self._pressed:
            direction -= right
        if 'E' in self._pressed:
            direction += up
        if 'Q' in self._pressed:
            direction -= up

        if direction.length_squared > 0.0:
            direction.normalize()
        return direction

    def _update_rotation(self, context, event):
        settings = self._settings(context)
        dx = event.mouse_x - self._last_mouse_x
        dy = event.mouse_y - self._last_mouse_y
        self._last_mouse_x = event.mouse_x
        self._last_mouse_y = event.mouse_y

        if dx == 0 and dy == 0:
            return

        current_rotation = self._rv3d.view_rotation.copy()
        yaw = Quaternion((0.0, 0.0, 1.0), -dx * settings.mouse_sensitivity)
        yawed_rotation = yaw @ current_rotation

        right_axis = yawed_rotation @ Vector((1.0, 0.0, 0.0))
        pitch = Quaternion(right_axis, dy * settings.mouse_sensitivity)

        rotation = pitch @ yawed_rotation
        rotation.normalize()
        self._rv3d.view_rotation = rotation

    def _update_motion(self, context):
        settings = self._settings(context)
        target_dir = self._target_direction()
        speed_limit = settings.max_speed * self._speed_scale * (settings.boost_multiplier if 'SHIFT' in self._pressed else 1.0)
        target_velocity = target_dir * speed_limit

        blend = min(1.0, settings.acceleration * settings.timer_step)
        self._velocity = self._velocity.lerp(target_velocity, blend)

        if target_dir.length_squared == 0.0:
            damping = max(0.0, 1.0 - settings.damping * settings.timer_step)
            self._velocity *= damping
            if self._velocity.length < 0.0005:
                self._velocity = Vector((0.0, 0.0, 0.0))

        self._rv3d.view_location += self._velocity * settings.timer_step

    def _finish(self, context):
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        if self._draw_handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(self._draw_handle, 'WINDOW')
            DRAW_HANDLES.discard(self._draw_handle)
            self._draw_handle = None
        if self._area:
            self._area.tag_redraw()
        self._pressed.clear()
        return {'FINISHED'}

    def invoke(self, context, event):
        settings = self._settings(context)
        self._reset_state()

        if settings is None or not settings.enabled:
            return {'PASS_THROUGH'}

        if context.area is None or context.area.type != 'VIEW_3D':
            return {'PASS_THROUGH'}

        if not self._capture_context(context):
            return {'CANCELLED'}

        self._enter_fps_view()
        self._released = False
        self._pressed.clear()
        self._velocity = Vector((0.0, 0.0, 0.0))
        self._speed_scale = 1.0
        self._nav_trigger = event.type
        self._last_mouse_x = event.mouse_x
        self._last_mouse_y = event.mouse_y
        self._timer = context.window_manager.event_timer_add(settings.timer_step, window=context.window)
        self._draw_handle = bpy.types.SpaceView3D.draw_handler_add(self._draw_overlay_callback, (context,), 'WINDOW', 'POST_PIXEL')
        DRAW_HANDLES.add(self._draw_handle)
        context.window_manager.modal_handler_add(self)
        log('Unity navigation started')
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if context.area != self._area:
            return self._finish(context)

        if event.type == 'MOUSEMOVE':
            self._update_rotation(context, event)
            self._area.tag_redraw()
            return {'RUNNING_MODAL'}

        if event.type == 'WHEELUPMOUSE' and event.value == 'PRESS':
            self._set_speed_scale(context, self._settings(context).scroll_speed_step)
            return {'RUNNING_MODAL'}

        if event.type == 'WHEELDOWNMOUSE' and event.value == 'PRESS':
            self._set_speed_scale(context, 1.0 / self._settings(context).scroll_speed_step)
            return {'RUNNING_MODAL'}

        if event.type == self._nav_trigger and event.value == 'RELEASE':
            self._released = True
            log(f'Unity navigation finished on {self._nav_trigger} release')
            return self._finish(context)

        if event.type in {'ESC'}:
            log('Unity navigation cancelled with ESC')
            return self._finish(context)

        keymap = {
            'W': 'W',
            'A': 'A',
            'S': 'S',
            'D': 'D',
            'Q': 'Q',
            'E': 'E',
            'LEFT_SHIFT': 'SHIFT',
            'RIGHT_SHIFT': 'SHIFT',
        }

        mapped = keymap.get(event.type)
        if mapped:
            if event.value == 'PRESS':
                self._pressed.add(mapped)
            elif event.value == 'RELEASE':
                self._pressed.discard(mapped)
            return {'RUNNING_MODAL'}

        if event.type == 'TIMER':
            self._update_motion(context)
            if self._overlay_until > 0.0:
                self._area.tag_redraw()
            return {'RUNNING_MODAL'}

        return {'RUNNING_MODAL'}


class UNITYNAV_OT_rebuild_keymap(Operator):
    bl_idname = 'unity_nav.rebuild_keymap'
    bl_label = 'Rebuild GameDev Navigation Keymap'
    bl_description = 'Re-register key bindings from the current add-on preferences'

    def execute(self, context):
        rebuild_keymaps(context)
        self.report({'INFO'}, 'GameDev Navigation keymap rebuilt')
        return {'FINISHED'}


class UNITYNAV_OT_apply_binding(Operator):
    bl_idname = 'unity_nav.apply_binding'
    bl_label = 'Apply Navigation Binding'
    bl_description = 'Apply the 3D View navigation binding to all add-on keymaps'

    def execute(self, context):
        km, kmi, _kc = find_navigation_keymap_item(context)
        if not kmi:
            self.report({'WARNING'}, 'Navigation keymap is not ready')
            return {'CANCELLED'}

        binding = keymap_binding(kmi)
        for target_km in find_navigation_keymaps(context):
            for target_kmi in target_km.keymap_items:
                if target_kmi.idname == 'view3d.unity_nav':
                    apply_keymap_binding(target_kmi, binding)
        self.report({'INFO'}, 'Navigation binding applied')
        return {'FINISHED'}


def safe_new(km, operator_id, key_type, event_value, **mods):
    try:
        kmi = km.keymap_items.new(operator_id, key_type, event_value, **mods)
        REGISTERED_KEYMAP_ITEMS.append((km, kmi))
        log(f'ADD    {operator_id} <- {key_type} {event_value} {mods}')
        return kmi
    except Exception as e:
        log(f'SKIP   {operator_id} <- {key_type} {event_value} {mods} | {e}')
        return None


def safe_prop(kmi, attr, value):
    if not kmi:
        return
    try:
        setattr(kmi.properties, attr, value)
    except Exception as e:
        log(f'PROP   skip {attr}={value} on {kmi.idname} | {e}')


def remove_items_by_operator(km, operator_ids):
    to_remove = [kmi for kmi in km.keymap_items if kmi.idname in operator_ids]
    for kmi in to_remove:
        try:
            log(f'REMOVE {kmi.idname} <- {kmi.type} {kmi.value}')
            km.keymap_items.remove(kmi)
        except Exception as e:
            log(f'REMOVE FAIL {kmi.idname} | {e}')


def remove_matching(km, operator_id=None, key_type=None, event_value=None):
    to_remove = []
    for kmi in km.keymap_items:
        if operator_id is not None and kmi.idname != operator_id:
            continue
        if key_type is not None and kmi.type != key_type:
            continue
        if event_value is not None and kmi.value != event_value:
            continue
        to_remove.append(kmi)

    for kmi in to_remove:
        try:
            log(f'REMOVE {kmi.idname} <- {kmi.type} {kmi.value}')
            km.keymap_items.remove(kmi)
        except Exception as e:
            log(f'REMOVE FAIL {kmi.idname} | {e}')


def get_target_keyconfig(context=None):
    context = context or bpy.context
    wm = getattr(context, 'window_manager', None)
    if wm is None:
        return None

    if wm.keyconfigs.addon:
        return wm.keyconfigs.addon
    if wm.keyconfigs.user:
        log('WARNING: Add-on keyconfig unavailable; falling back to user keyconfig')
        return wm.keyconfigs.user
    return None


def find_keymap(kc, name, space_type='EMPTY'):
    for km in kc.keymaps:
        if km.name == name and km.space_type == space_type:
            return km
    return None


def get_or_create_keymap(kc, name, space_type='EMPTY', region_type='WINDOW'):
    return find_keymap(kc, name, space_type) or kc.keymaps.new(
        name=name,
        space_type=space_type,
        region_type=region_type,
    )


def find_navigation_keymap_item(context=None):
    kc = get_target_keyconfig(context)
    if not kc:
        return None, None, None
    km = find_keymap(kc, '3D View', 'VIEW_3D')
    if not km:
        return None, None, kc
    for kmi in km.keymap_items:
        if kmi.idname == 'view3d.unity_nav':
            return km, kmi, kc
    return km, None, kc


def find_navigation_keymaps(context=None):
    kc = get_target_keyconfig(context)
    if not kc:
        return []
    targets = (
        ('3D View', 'VIEW_3D'),
        ('Object Mode', 'EMPTY'),
        ('Mesh', 'EMPTY'),
    )
    return [
        km for name, space_type in targets
        if (km := find_keymap(kc, name, space_type)) is not None
    ]


def keymap_binding(kmi):
    if not kmi:
        return DEFAULT_NAV_TRIGGER, False, False, False, False
    return (
        kmi.type,
        kmi.shift,
        kmi.ctrl,
        kmi.alt,
        kmi.oskey,
    )


def apply_keymap_binding(kmi, binding):
    key_type, shift, ctrl, alt, oskey = binding
    kmi.type = key_type
    kmi.value = 'PRESS'
    kmi.shift = shift
    kmi.ctrl = ctrl
    kmi.alt = alt
    kmi.oskey = oskey


def clear_registered_keymap_items():
    while REGISTERED_KEYMAP_ITEMS:
        km, kmi = REGISTERED_KEYMAP_ITEMS.pop()
        try:
            km.keymap_items.remove(kmi)
        except Exception:
            pass


def unregister_keymaps(context=None):
    clear_registered_keymap_items()

    kc = get_target_keyconfig(context)
    if not kc:
        return

    targets = (
        ('3D View', 'VIEW_3D'),
        ('Object Mode', 'EMPTY'),
        ('Mesh', 'EMPTY'),
    )
    for name, space_type in targets:
        km = find_keymap(kc, name, space_type)
        if km is not None:
            remove_items_by_operator(km, ['view3d.unity_nav'])


def apply_common_view_bindings(km, settings, binding=None):
    log(f'Apply bindings to keymap: {km.name}')
    remove_items_by_operator(km, ['view3d.unity_nav'])

    if settings.enable_cursor_shortcut:
        safe_new(
            km,
            'view3d.cursor3d',
            settings.cursor_trigger,
            'CLICK',
            shift=DEFAULT_CURSOR_MOD_SHIFT,
        )
    key_type, shift, ctrl, alt, oskey = binding or (
        settings.nav_trigger, False, False, False, False
    )
    safe_new(
        km,
        'view3d.unity_nav',
        key_type,
        'PRESS',
        shift=shift,
        ctrl=ctrl,
        alt=alt,
        oskey=oskey,
    )


def register_keymaps(context=None):
    context = context or bpy.context
    previous = find_navigation_keymap_item(context)[1]
    binding = keymap_binding(previous) if previous else None
    unregister_keymaps(context)
    settings = get_preferences(context)

    if settings is None or not settings.enabled:
        log('Skip keymap registration because addon is disabled or unavailable')
        return

    kc = get_target_keyconfig(context)
    if not kc:
        log('ERROR: No add-on keyconfig found.')
        return

    target_keymaps = [
        get_or_create_keymap(kc, '3D View', 'VIEW_3D', 'WINDOW'),
        get_or_create_keymap(kc, 'Object Mode', 'EMPTY', 'WINDOW'),
        get_or_create_keymap(kc, 'Mesh', 'EMPTY', 'WINDOW'),
    ]

    seen = set()
    for km in target_keymaps:
        key = (km.name, km.space_type, km.region_type)
        if key in seen:
            continue
        seen.add(key)
        apply_common_view_bindings(km, settings, binding)


def rebuild_keymaps(context=None):
    context = context or bpy.context
    if get_target_keyconfig(context) is None or get_preferences(context) is None:
        if not bpy.app.timers.is_registered(deferred_register_keymaps):
            bpy.app.timers.register(deferred_register_keymaps, first_interval=0.1)
        return
    register_keymaps(context)


CLASSES = (
    UnityNavPreferences,
    VIEW3D_OT_unity_nav,
    UNITYNAV_OT_rebuild_keymap,
    UNITYNAV_OT_apply_binding,
)


def deferred_register_keymaps():
    context = bpy.context
    if get_target_keyconfig(context) is None or get_preferences(context) is None:
        return 0.1

    register_keymaps(context)
    return None


def register():
    try:
        bpy.app.translations.unregister(TRANSLATION_ID)
    except RuntimeError:
        pass
    translations = load_translations()
    if translations:
        bpy.app.translations.register(TRANSLATION_ID, translations)

    try:
        for cls in CLASSES:
            bpy.utils.register_class(cls)
    except Exception:
        if translations:
            bpy.app.translations.unregister(TRANSLATION_ID)
        raise

    if not bpy.app.timers.is_registered(deferred_register_keymaps):
        bpy.app.timers.register(deferred_register_keymaps, first_interval=0.0)
    log('GameDev Navigation addon registered')


def unregister():
    if bpy.app.timers.is_registered(deferred_register_keymaps):
        bpy.app.timers.unregister(deferred_register_keymaps)
    unregister_keymaps()
    for handle in list(DRAW_HANDLES):
        try:
            bpy.types.SpaceView3D.draw_handler_remove(handle, 'WINDOW')
        except Exception:
            pass
        DRAW_HANDLES.discard(handle)
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
    try:
        bpy.app.translations.unregister(TRANSLATION_ID)
    except RuntimeError:
        pass
    log('GameDev Navigation addon unregistered')


if __name__ == '__main__':
    register()
