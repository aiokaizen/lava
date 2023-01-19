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
        if 'admin_interface' not in sys.modules:
            logging.error("Admin interface is not installed in this project!")
            return
        
        default_theme_name = "EKBlocks default theme"
        
        try:
            theme = Theme.objects.get(name=default_theme_name)
            logging.warning("Default theme already exists.")
        except Theme.DoesNotExist:
            theme = Theme(
                name=default_theme_name,
                active=True,
                title="This is a test",
                title_visible=False,
                logo_max_width=150,
                logo_max_height=80,
                env_name="EKBlocks",
                env_visible_in_header=True,
                env_visible_in_favicon=True,
                language_chooser_active=True,
                language_chooser_control="default-select",
                language_chooser_display="code",
                css_module_rounded_corners=True,
                related_modal_active=True,
                related_modal_rounded_corners=True,
                related_modal_close_button_visible=True,
                list_filter_highlight=True,
                list_filter_dropdown=True,
                list_filter_sticky=True,
                list_filter_removal_links=False,
                foldable_apps=True,
                show_fieldsets_as_tabs=False,
                show_inlines_as_tabs=False,
                recent_actions_visible=True,
                form_submit_sticky=False,
                form_pagination_sticky=False,
                
                # Default colors
                title_color="#FFFFFF",
                logo_color="#FFFFFF",
                env_color="#E74C3C",

                # Header colors
                css_header_background_color="#11123A",
                css_header_text_color="#FFFFFF",
                css_header_link_color="#FFFFFF",
                css_header_link_hover_color="#1CAB98",

                # Breadcrumbs colors
                css_module_background_color="#1CAB98",
                css_module_background_selected_color="#FFFDEE",
                css_module_text_color="#FFFFFF",
                css_module_link_color="#FFFFFF",
                css_module_link_selected_color="#FFFFFF",
                css_module_link_hover_color="#11123A",

                # Generic links colors
                css_generic_link_color="#11123A",
                css_generic_link_hover_color="#1CAB98",

                # Buttons colors
                css_save_button_background_color="#1CAB98",
                css_save_button_background_hover_color="#11123A",
                css_save_button_text_color="#FFFFFF",

                css_delete_button_background_color="#BA2121",
                css_delete_button_background_hover_color="#A41515",
                css_delete_button_text_color="#FFFFFF",

                # Modal colors
                related_modal_background_color="#11123A",
                related_modal_background_opacity="0.2",
            )

            theme.save()
            favicon_path = os.path.join(
                settings.BASE_DIR,
                'lava/static/lava/assets/images/logo/favicon.png'
            )
            logo_path = os.path.join(
                settings.BASE_DIR,
                'lava/static/lava/assets/images/logo/logo_hybrid_white.png'
            )
            with open(logo_path, 'rb') as logo_file:
                theme.logo.save(
                    "logo.png",
                    File(logo_file)
                )
            with open(favicon_path, 'rb') as favicon:
                theme.favicon.save(
                    "favicon.png",
                    File(favicon)
                )
            logging.info("The default theme has been initialized successfully.")
