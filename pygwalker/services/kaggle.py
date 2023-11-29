from functools import lru_cache

from pygwalker.services.global_var import GlobalVarManager
from pygwalker.utils.display import display_html


# pylint: disable=import-outside-toplevel
# pylint: disable=broad-exception-caught
def auto_set_kanaries_api_key_on_kaggle():
    """Auto set kanaries api key on kaggle."""
    from kaggle_secrets import UserSecretsClient
    if not GlobalVarManager.kanaries_api_key:
        try:
            GlobalVarManager.set_kanaries_api_key(
                UserSecretsClient().get_secret("kanaries_api_key")
            )
        except Exception:
            pass


@lru_cache()
def adjust_kaggle_default_font_size():
    """Adjust kaggle default font size."""
    display_html("""<style>html {font-size: 16px;}</style>""")


def show_tips_user_kaggle() -> bool:
    """Whether has set kanaries api key."""
    from kaggle_secrets import UserSecretsClient
    try:
        has_set_api_key = bool(UserSecretsClient().get_secret("kanaries_api_key"))
    except Exception:
        has_set_api_key = False

    tips = """
        <p>Since you haven't set the kannaries_api_key, Pygwalker assumes it's your first time using it on Kaggle.</p>
        <p>Due to the persistent file approach in Kaggle, there may be some impact on the user experience when using Pygwalker on Kaggle.</p>
        <p>Please take a moment to read this article: <a href="https://github.com/Kanaries/pygwalker/wiki/Best-Practices-for-Using-Pygwalker-in-Kaggle">Best Practices for Using Pygwalker in Kaggle</a>, which can help you optimize your Pygwalker experience on Kaggle.</p>
    """

    if not has_set_api_key:
        display_html(tips)
