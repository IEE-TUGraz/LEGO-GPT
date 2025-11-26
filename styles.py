"""
Styles Module for LEGO-GPT

This module provides centralized style definitions for the Dash application.
All UI styling is configured here for easy customization and maintenance.
"""

from dataclasses import dataclass, field
from typing import Optional


# =============================================================================
# Theme Configuration
# =============================================================================

@dataclass
class ThemeColors:
    """
    Theme color definitions.

    Change these values to customize the application's color scheme.
    """
    # Primary colors
    primary: str = "#6BA3A3"
    primary_light: str = "#8DBCBC"
    primary_dark: str = "#4A8A8A"

    # Secondary colors
    secondary: str = "#E1EDED"
    secondary_light: str = "#F5F9F9"
    secondary_dark: str = "#C5D7D7"

    # Accent colors
    accent: str = "#2E86AB"
    accent_light: str = "#5AA3C4"
    accent_dark: str = "#1D6A8A"

    # Neutral colors
    background: str = "#6BA3A3"
    surface: str = "#FFFFFF"
    surface_alt: str = "#F8FAFA"

    # Text colors
    text_primary: str = "#333333"
    text_secondary: str = "#666666"
    text_light: str = "#999999"
    text_inverse: str = "#FFFFFF"

    # Border colors
    border: str = "#E0E0E0"
    border_light: str = "#F0F0F0"
    border_dark: str = "#CCCCCC"

    # Semantic colors
    success: str = "#2ECC71"
    success_light: str = "#82E3AA"
    warning: str = "#F39C12"
    warning_light: str = "#F7C873"
    error: str = "#E74C3C"
    error_light: str = "#F1948A"
    info: str = "#3498DB"
    info_light: str = "#85C1E9"


@dataclass
class ThemeSpacing:
    """Spacing values for consistent layout."""
    xs: str = "4px"
    sm: str = "8px"
    md: str = "12px"
    lg: str = "16px"
    xl: str = "24px"
    xxl: str = "32px"
    xxxl: str = "48px"


@dataclass
class ThemeBorderRadius:
    """Border radius values."""
    sm: str = "4px"
    md: str = "6px"
    lg: str = "8px"
    xl: str = "12px"
    round: str = "50%"


@dataclass
class ThemeTypography:
    """Typography settings."""
    font_family: str = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    font_size_xs: str = "10px"
    font_size_sm: str = "12px"
    font_size_md: str = "14px"
    font_size_lg: str = "16px"
    font_size_xl: str = "20px"
    font_size_xxl: str = "24px"
    font_weight_normal: int = 400
    font_weight_medium: int = 500
    font_weight_semibold: int = 600
    font_weight_bold: int = 700
    line_height: float = 1.5


@dataclass
class ThemeShadows:
    """Box shadow definitions."""
    sm: str = "0 1px 2px rgba(0, 0, 0, 0.05)"
    md: str = "0 2px 4px rgba(0, 0, 0, 0.1)"
    lg: str = "0 4px 8px rgba(0, 0, 0, 0.12)"
    xl: str = "0 8px 16px rgba(0, 0, 0, 0.15)"


@dataclass
class Theme:
    """Complete theme configuration."""
    colors: ThemeColors = field(default_factory=ThemeColors)
    spacing: ThemeSpacing = field(default_factory=ThemeSpacing)
    radius: ThemeBorderRadius = field(default_factory=ThemeBorderRadius)
    typography: ThemeTypography = field(default_factory=ThemeTypography)
    shadows: ThemeShadows = field(default_factory=ThemeShadows)


# Default theme instance
theme = Theme()


# =============================================================================
# Component Styles
# =============================================================================

class Styles:
    """
    Centralized style definitions for all UI components.

    Usage:
        from styles import styles
        html.Div(style=styles.container)
    """

    def __init__(self, t: Theme = theme):
        """Initialize styles with a theme."""
        self._theme = t

    # =========================================================================
    # Layout Containers
    # =========================================================================

    @property
    def app_container(self) -> dict:
        """Main application container style."""
        return {
            "backgroundColor": self._theme.colors.background,
            "minHeight": "100vh",
            "padding": self._theme.spacing.md,
            "fontFamily": self._theme.typography.font_family,
        }

    @property
    def control_row(self) -> dict:
        """Top control row container."""
        return {
            "display": "flex",
            "alignItems": "center",
            "marginBottom": self._theme.spacing.md,
            "justifyContent": "space-between",
            "flexWrap": "wrap",
            "gap": self._theme.spacing.md,
        }

    @property
    def control_group_left(self) -> dict:
        """Left control group container."""
        return {
            "display": "flex",
            "alignItems": "center",
            "flex": "1",
            "gap": self._theme.spacing.lg,
            "minWidth": "0",
            "maxWidth": "50%",
        }

    @property
    def control_group_right(self) -> dict:
        """Right control group container."""
        return {
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "flex-start",
            "width": "50%",
            "gap": self._theme.spacing.md,
        }

    @property
    def main_content(self) -> dict:
        """Main content area (map + graph)."""
        return {
            "display": "flex",
            "gap": self._theme.spacing.md,
            "height": "calc(100vh - 150px)",
            "flexWrap": "wrap",
            "minHeight": "500px",
        }

    @property
    def panel(self) -> dict:
        """Generic panel style."""
        return {
            "flex": "1",
            "minWidth": "0",
            "backgroundColor": self._theme.colors.surface,
            "borderRadius": self._theme.radius.lg,
            "boxShadow": self._theme.shadows.md,
            "overflow": "hidden",
        }

    @property
    def map_container(self) -> dict:
        """Map container style."""
        return {
            **self.panel,
            "height": "100%",
        }

    @property
    def graph_container(self) -> dict:
        """Graph container style."""
        return {
            **self.panel,
            "height": "100%",
            "padding": self._theme.spacing.sm,
        }

    # =========================================================================
    # Component Styles
    # =========================================================================

    @property
    def card(self) -> dict:
        """Card/panel with shadow."""
        return {
            "backgroundColor": self._theme.colors.surface,
            "borderRadius": self._theme.radius.lg,
            "boxShadow": self._theme.shadows.md,
            "padding": self._theme.spacing.md,
        }

    @property
    def dropdown(self) -> dict:
        """Standard dropdown style."""
        return {
            "width": "140px",
            "fontWeight": self._theme.typography.font_weight_medium,
            "fontSize": self._theme.typography.font_size_md,
        }

    @property
    def dropdown_wide(self) -> dict:
        """Wide dropdown style."""
        return {
            **self.dropdown,
            "width": "180px",
        }

    @property
    def dropdown_narrow(self) -> dict:
        """Narrow dropdown style."""
        return {
            **self.dropdown,
            "width": "120px",
        }

    @property
    def button(self) -> dict:
        """Standard button style."""
        return {
            "minWidth": "80px",
            "padding": f"{self._theme.spacing.sm} {self._theme.spacing.md}",
            "fontWeight": self._theme.typography.font_weight_semibold,
            "fontSize": self._theme.typography.font_size_md,
            "borderRadius": self._theme.radius.md,
            "border": f"1px solid {self._theme.colors.border}",
            "backgroundColor": self._theme.colors.surface,
            "color": self._theme.colors.text_primary,
            "cursor": "pointer",
            "transition": "all 0.2s ease",
        }

    @property
    def button_primary(self) -> dict:
        """Primary button style."""
        return {
            **self.button,
            "backgroundColor": self._theme.colors.accent,
            "color": self._theme.colors.text_inverse,
            "border": "none",
        }

    @property
    def button_small(self) -> dict:
        """Small button style."""
        return {
            **self.button,
            "minWidth": "60px",
            "padding": f"{self._theme.spacing.xs} {self._theme.spacing.sm}",
            "fontSize": self._theme.typography.font_size_sm,
        }

    @property
    def input_number(self) -> dict:
        """Number input style."""
        return {
            "width": "70px",
            "padding": self._theme.spacing.sm,
            "borderRadius": self._theme.radius.sm,
            "border": f"1px solid {self._theme.colors.border}",
            "fontSize": self._theme.typography.font_size_md,
        }

    @property
    def label(self) -> dict:
        """Label style."""
        return {
            "fontSize": self._theme.typography.font_size_sm,
            "fontWeight": self._theme.typography.font_weight_medium,
            "color": self._theme.colors.text_secondary,
            "marginBottom": self._theme.spacing.xs,
        }

    # =========================================================================
    # Slider Styles
    # =========================================================================

    @property
    def slider_container(self) -> dict:
        """Slider container style."""
        return {
            "flex": "1",
            "display": "flex",
            "alignItems": "center",
            "gap": self._theme.spacing.md,
            "minWidth": "200px",
        }

    @property
    def range_slider_container(self) -> dict:
        """Range slider container style."""
        return {
            "flex": "1",
            "minWidth": "200px",
        }

    # =========================================================================
    # Map & Graph Styles
    # =========================================================================

    @property
    def map(self) -> dict:
        """Map component style."""
        return {
            "height": "100%",
            "width": "100%",
            "borderRadius": self._theme.radius.lg,
        }

    @property
    def graph(self) -> dict:
        """Graph component style."""
        return {
            "width": "100%",
            "height": "100%",
        }

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def with_margin(
            self,
            base_style: dict,
            top: Optional[str] = None,
            right: Optional[str] = None,
            bottom: Optional[str] = None,
            left: Optional[str] = None
    ) -> dict:
        """Add margins to a style."""
        result = base_style.copy()
        if top:
            result["marginTop"] = top
        if right:
            result["marginRight"] = right
        if bottom:
            result["marginBottom"] = bottom
        if left:
            result["marginLeft"] = left
        return result

    def with_padding(
            self,
            base_style: dict,
            value: str
    ) -> dict:
        """Set padding on a style."""
        return {**base_style, "padding": value}

    def hidden(self) -> dict:
        """Hidden element style."""
        return {"display": "none"}

    def visible(self, display: str = "block") -> dict:
        """Visible element style."""
        return {"display": display}


# =============================================================================
# Component Wrapper Styles
# =============================================================================

class ComponentStyles:
    """Factory methods for component wrapper styles."""

    def __init__(self, t: Theme = theme):
        """Initialize with theme."""
        self._theme = t

    def dropdown_wrapper(
            self,
            margin_right: Optional[str] = None,
            display: str = "flex"
    ) -> dict:
        """Wrapper for dropdown components."""
        style = {
            "display": display,
            "flexDirection": "column",
            "gap": self._theme.spacing.xs,
        }
        if margin_right:
            style["marginRight"] = margin_right
        return style

    def button_wrapper(
            self,
            margin_right: Optional[str] = None
    ) -> dict:
        """Wrapper for button components."""
        style = {
            "display": "flex",
            "flexDirection": "column",
            "gap": self._theme.spacing.xs,
        }
        if margin_right:
            style["marginRight"] = margin_right
        return style

    def slider_wrapper(self) -> dict:
        """Wrapper for slider components."""
        return {
            "flex": "1",
            "minWidth": "200px",
        }

    def input_wrapper(self, display: str = "block") -> dict:
        """Wrapper for input components."""
        return {
            "display": display,
            "flex": "none",
        }

    def flex_row(
            self,
            gap: Optional[str] = None,
            align: str = "center",
            justify: str = "flex-start",
            wrap: bool = False
    ) -> dict:
        """Flexbox row layout."""
        return {
            "display": "flex",
            "flexDirection": "row",
            "alignItems": align,
            "justifyContent": justify,
            "gap": gap or self._theme.spacing.md,
            "flexWrap": "wrap" if wrap else "nowrap",
        }

    def flex_column(
            self,
            gap: Optional[str] = None,
            align: str = "stretch"
    ) -> dict:
        """Flexbox column layout."""
        return {
            "display": "flex",
            "flexDirection": "column",
            "alignItems": align,
            "gap": gap or self._theme.spacing.md,
        }

    def grid(
            self,
            columns: str = "1fr 1fr",
            gap: Optional[str] = None
    ) -> dict:
        """CSS Grid layout."""
        return {
            "display": "grid",
            "gridTemplateColumns": columns,
            "gap": gap or self._theme.spacing.md,
        }


# =============================================================================
# Singleton Instances
# =============================================================================

# Global styles instance for easy access
styles = Styles()
component_styles = ComponentStyles()


# =============================================================================
# Utility Functions
# =============================================================================

def create_custom_theme(
        primary: Optional[str] = None,
        accent: Optional[str] = None,
        background: Optional[str] = None
) -> Theme:
    """
    Create a custom theme with overridden colors.

    Args:
        primary: Primary color override.
        accent: Accent color override.
        background: Background color override.

    Returns:
        Custom Theme instance.
    """
    colors = ThemeColors()

    if primary:
        colors.primary = primary
    if accent:
        colors.accent = accent
    if background:
        colors.background = background

    return Theme(colors=colors)


def get_styles_for_theme(custom_theme: Theme) -> Styles:
    """
    Get a Styles instance for a custom theme.

    Args:
        custom_theme: Custom Theme instance.

    Returns:
        Styles instance configured with the custom theme.
    """
    return Styles(custom_theme)
