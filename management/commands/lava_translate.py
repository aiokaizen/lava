import os
import logging
import subprocess

import polib
from translate import Translator

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command
from django.utils.translation import trans_real


class Command(BaseCommand):
    help = """
        This command Generates translation files and translates all strings using
        the `translate` library.
        example usage:
        >>> python manage.py lava_translate -l en_US,fr_FR,ar_MA -n lava
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-l', '--locales',
            required=True,
            type=str,
            help="The local languages to translate to separated by commas(eg: en,fr_FR,ar,en_GB,...)."
        )
        parser.add_argument(
            '-n', '--app-name',
            required=True,
            type=str,
            help='The name of the django application to be translated.',
        )
        parser.add_argument(
            '-g', '--generate-translations',
            action='store_true',
            help="Automatically generate translations using AI."
        )
        parser.add_argument(
            '-s', '--source-language',
            type=str,
            default="en",
            help="Set the source languange (primary language of the app - defaults to 'en')."
        )

    def handle(self, *args, **options):
        # Create some demo content here

        # Getting user input
        locales = options["locales"].split(',')
        app_name = options["app_name"]
        generate_translations = options["generate_translations"]
        source_language =  options["source_language"]

        # logging.info(
        print(
            "Start generating translations with the following parameters:\n"
            f"\t-locales={locales}\n"
            f"\t-app_name={app_name}\n"
            f"\t-generate_translations={generate_translations}\n"
            f"\t-source_language={source_language}\n"
        )

        base_dir = settings.BASE_DIR

        # Generate base po files
        # trans_real.activate(source_language)
        # with open(os.path.join(base_dir, 'tmp', 'out.tmp'), 'w') as output:
        #     process = subprocess.Popen(
        #         [f". ./makemessages.sh", " ", f"{app_name}", *locales],
        #         stdout=output,
        #         # shell=True
        #     )
        #     process.wait()

        # if not generate_translations:
        #     return

        # Automatically translate po files
        for locale in locales:
            locale_po_filename = os.path.join(
                base_dir, app_name, "locale", locale, "LC_MESSAGES", "django.po"
            )
            if not os.path.exists(locale_po_filename):
                print(f"\n\nlocale `{locale}` is not a valid local name!\n")
                return

            # Load the .po file
            po_file = polib.pofile(locale_po_filename)

            # Create a translator object
            translator = Translator(
                to_lang=locale.replace('_', '-'),
                from_lang=source_language.replace('_', '-')
            )

            # Translate each message in the .po file
            for entry in po_file:
                print(f"translating `{entry.msgid}` from English to {locale}")
                entry.msgstr = translator.translate(entry.msgid)
                print("translation:", entry.msgstr, '\n\n')

            # Save the translated .po file
            # po_file.save(locale_po_filename)
            po_file.save(os.path.join(
                base_dir, app_name, "locale", locale, "LC_MESSAGES", "auto_generated.po"
            ))
