import sys
import os
import logging

from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings

from admin_interface.models import Theme


class Command(BaseCommand):
    help = """
        This command creates a default theme and activates it.
    """

    def handle(self, *args, **options):
        if "admin_interface" not in sys.modules:
            logging.error("Admin interface is not installed in this project!")
            return

        # Setup defaults
        default_theme_name = "EKBlocks default theme"
        title = "This is a test"
        title_visible = False
        logo_max_width = 150
        logo_max_height = 80
        env_name = "EKBlocks"
        env_visible_in_header = False
        env_visible_in_favicon = False
        language_chooser_active = True
        language_chooser_control = "default-select"
        language_chooser_display = "code"
        css_module_rounded_corners = True
        related_modal_active = True
        related_modal_rounded_corners = True
        related_modal_close_button_visible = True
        list_filter_highlight = True
        list_filter_dropdown = True
        list_filter_sticky = True
        list_filter_removal_links = False
        foldable_apps = True
        show_fieldsets_as_tabs = False
        show_inlines_as_tabs = False
        recent_actions_visible = True
        form_submit_sticky = True
        form_pagination_sticky = False
        title_color = "#FFFFFF"
        logo_color = "#FFFFFF"
        env_color = "#E74C3C"
        css_header_background_color = "#11123A"
        css_header_text_color = "#FFFFFF"
        css_header_link_color = "#FFFFFF"
        css_header_link_hover_color = "#1CAB98"
        css_module_background_color = "#1CAB98"
        css_module_background_selected_color = "#FFFDEE"
        css_module_text_color = "#FFFFFF"
        css_module_link_color = "#FFFFFF"
        css_module_link_selected_color = "#FFFFFF"
        css_module_link_hover_color = "#11123A"
        css_generic_link_color = "#11123A"
        css_generic_link_hover_color = "#1CAB98"
        css_save_button_background_color = "#1CAB98"
        css_save_button_background_hover_color = "#11123A"
        css_save_button_text_color = "#FFFFFF"
        css_delete_button_background_color = "#BA2121"
        css_delete_button_background_hover_color = "#A41515"
        css_delete_button_text_color = "#FFFFFF"
        related_modal_background_color = "#11123A"
        related_modal_background_opacity = "0.2"

        favicon_path = os.path.join(
            settings.BASE_DIR, "lava/static/lava/assets/images/logo/favicon.png"
        )

        logo_path = os.path.join(
            settings.BASE_DIR,
            "lava/static/lava/assets/images/logo/logo_hybrid_white.png",
        )

        try:
            theme = Theme.objects.get(name=default_theme_name)
            theme.name = default_theme_name
            theme.title = title
            theme.title_visible = title_visible
            theme.logo_max_width = logo_max_width
            theme.logo_max_height = logo_max_height
            theme.env_name = env_name
            theme.env_visible_in_header = env_visible_in_header
            theme.env_visible_in_favicon = env_visible_in_favicon
            theme.language_chooser_active = language_chooser_active
            theme.language_chooser_control = language_chooser_control
            theme.language_chooser_display = language_chooser_display
            theme.css_module_rounded_corners = css_module_rounded_corners
            theme.related_modal_active = related_modal_active
            theme.related_modal_rounded_corners = related_modal_rounded_corners
            theme.related_modal_close_button_visible = (
                related_modal_close_button_visible
            )
            theme.list_filter_highlight = list_filter_highlight
            theme.list_filter_dropdown = list_filter_dropdown
            theme.list_filter_sticky = list_filter_sticky
            theme.list_filter_removal_links = list_filter_removal_links
            theme.foldable_apps = foldable_apps
            theme.show_fieldsets_as_tabs = show_fieldsets_as_tabs
            theme.show_inlines_as_tabs = show_inlines_as_tabs
            theme.recent_actions_visible = recent_actions_visible
            theme.form_submit_sticky = form_submit_sticky
            theme.form_pagination_sticky = form_pagination_sticky
            theme.title_color = title_color
            theme.logo_color = logo_color
            theme.env_color = env_color
            theme.css_header_background_color = css_header_background_color
            theme.css_header_text_color = css_header_text_color
            theme.css_header_link_color = css_header_link_color
            theme.css_header_link_hover_color = css_header_link_hover_color
            theme.css_module_background_color = css_module_background_color
            theme.css_module_background_selected_color = (
                css_module_background_selected_color
            )
            theme.css_module_text_color = css_module_text_color
            theme.css_module_link_color = css_module_link_color
            theme.css_module_link_selected_color = css_module_link_selected_color
            theme.css_module_link_hover_color = css_module_link_hover_color
            theme.css_generic_link_color = css_generic_link_color
            theme.css_generic_link_hover_color = css_generic_link_hover_color
            theme.css_save_button_background_color = css_save_button_background_color
            theme.css_save_button_background_hover_color = (
                css_save_button_background_hover_color
            )
            theme.css_save_button_text_color = css_save_button_text_color
            theme.css_delete_button_background_color = (
                css_delete_button_background_color
            )
            theme.css_delete_button_background_hover_color = (
                css_delete_button_background_hover_color
            )
            theme.css_delete_button_text_color = css_delete_button_text_color
            theme.related_modal_background_color = related_modal_background_color
            theme.related_modal_background_opacity = related_modal_background_opacity
            theme.save()
            theme.logo.delete()
            theme.set_active()
            theme.favicon.delete()
            with open(logo_path, "rb") as logo_file:
                theme.logo.save("logo.png", File(logo_file))
            with open(favicon_path, "rb") as favicon:
                theme.favicon.save("favicon.png", File(favicon))
        except Theme.DoesNotExist:
            theme = Theme(
                name=default_theme_name,
                title=title,
                title_visible=title_visible,
                logo_max_width=logo_max_width,
                logo_max_height=logo_max_height,
                env_name=env_name,
                env_visible_in_header=env_visible_in_header,
                env_visible_in_favicon=env_visible_in_favicon,
                language_chooser_active=language_chooser_active,
                language_chooser_control=language_chooser_control,
                language_chooser_display=language_chooser_display,
                css_module_rounded_corners=css_module_rounded_corners,
                related_modal_active=related_modal_active,
                related_modal_rounded_corners=related_modal_rounded_corners,
                related_modal_close_button_visible=related_modal_close_button_visible,
                list_filter_highlight=list_filter_highlight,
                list_filter_dropdown=list_filter_dropdown,
                list_filter_sticky=list_filter_sticky,
                list_filter_removal_links=list_filter_removal_links,
                foldable_apps=foldable_apps,
                show_fieldsets_as_tabs=show_fieldsets_as_tabs,
                show_inlines_as_tabs=show_inlines_as_tabs,
                recent_actions_visible=recent_actions_visible,
                form_submit_sticky=form_submit_sticky,
                form_pagination_sticky=form_pagination_sticky,
                # Default colors
                title_color=title_color,
                logo_color=logo_color,
                env_color=env_color,
                # Header colors
                css_header_background_color=css_header_background_color,
                css_header_text_color=css_header_text_color,
                css_header_link_color=css_header_link_color,
                css_header_link_hover_color=css_header_link_hover_color,
                # Breadcrumbs colors
                css_module_background_color=css_module_background_color,
                css_module_background_selected_color=css_module_background_selected_color,
                css_module_text_color=css_module_text_color,
                css_module_link_color=css_module_link_color,
                css_module_link_selected_color=css_module_link_selected_color,
                css_module_link_hover_color=css_module_link_hover_color,
                css_generic_link_color=css_generic_link_color,
                css_generic_link_hover_color=css_generic_link_hover_color,
                css_save_button_background_color=css_save_button_background_color,
                css_save_button_background_hover_color=css_save_button_background_hover_color,
                css_save_button_text_color=css_save_button_text_color,
                css_delete_button_background_color=css_delete_button_background_color,
                css_delete_button_background_hover_color=css_delete_button_background_hover_color,
                css_delete_button_text_color=css_delete_button_text_color,
                related_modal_background_color=related_modal_background_color,
                related_modal_background_opacity=related_modal_background_opacity,
            )

            theme.save()
            theme.set_active()

            with open(logo_path, "rb") as logo_file:
                theme.logo.save("logo.png", File(logo_file))
            with open(favicon_path, "rb") as favicon:
                theme.favicon.save("favicon.png", File(favicon))
            logging.info("The default theme has been initialized successfully.")
