# Microsoft-Style Newsletter Template Guide

## Overview

This directory contains the Microsoft-style technical newsletter HTML template used by the Enterprise Newsletter Generator. The template is designed to match Microsoft's Fluent Design System and technical blog aesthetic.

## Template File

**`microsoft_newsletter_template.html`** - The main newsletter template

## Design Features

### Color Palette (Microsoft Fluent Design)

- **Primary Blue**: `#0078D4` - Microsoft's signature blue
- **Dark Blue**: `#005A9E` - Headers and emphasis
- **Light Blue**: `#50E6FF` - Accents
- **Grays**: Multiple shades for backgrounds and text
- **Green**: `#107C10` - Action items and success states
- **Orange**: `#D83B01` - Call-to-action boxes

### Typography

- **Font Family**: Segoe UI (Microsoft's standard font)
- **Fallbacks**: -apple-system, BlinkMacSystemFont, Roboto, Helvetica Neue
- **Font Sizes**: Hierarchical sizing from 32px (main title) to 13px (footer)

### Layout Components

#### 1. Header Section
- Gradient blue background
- Logo with colored square icon
- Main title (32px)
- Subtitle (18px)
- Date stamp

#### 2. Executive Summary
- Left blue border accent
- Light gray background
- Prominent placement at top

#### 3. Key Highlights
- Card-based layout
- Hover effects (transform + shadow)
- Left blue border accent
- Title + description format

#### 4. Feature Articles
- White cards with subtle border
- Structured sections:
  - Context / Problem Statement
  - Key Ideas or Architecture
  - Benefits & Trade-offs
  - Recommended Best Practices
  - Call to Action (orange accent box)

#### 5. Quick Bites
- Bulleted list with custom blue bullets
- Light gray background
- Compact format

#### 6. Action Items
- Green accent (success color)
- Organized by audience:
  - Engineering Teams
  - Architecture / Strategy Teams
  - Leadership / Decision Makers
- Checkmark bullets

#### 7. Technology Tags
- Blue pill-shaped tags
- Flexbox layout for wrapping
- Clean, modern appearance

#### 8. Best Practices
- Light bulb emoji bullets
- Gray background
- Easy-to-scan format

#### 9. Footer
- Dark gray background
- Centered text
- Timestamp

## Template Placeholders

The template uses the following placeholders that are replaced by the generator:

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{TITLE}}` | Newsletter main title | "Technology Newsletter" |
| `{{SUBTITLE}}` | Newsletter subtitle | "Enterprise IT Update" |
| `{{DATE}}` | Publication date | "November 11, 2025" |
| `{{EXECUTIVE_SUMMARY}}` | Executive summary HTML | `<p>Summary text...</p>` |
| `{{KEY_HIGHLIGHTS}}` | Key highlights cards HTML | Multiple highlight cards |
| `{{FEATURE_ARTICLES}}` | Feature articles HTML | Complete article sections |
| `{{QUICK_BITES}}` | Quick bites list HTML | `<ul><li>...</li></ul>` |
| `{{ACTION_ITEMS}}` | Action items HTML | Organized by audience |
| `{{TECHNOLOGIES}}` | Technology tags HTML | Pill-shaped tags |
| `{{BEST_PRACTICES}}` | Best practices HTML | Bulleted list |
| `{{FOOTER_DATE}}` | Footer timestamp | "November 11, 2025 at 2:30 PM" |

## Responsive Design

The template includes responsive breakpoints:

```css
@media (max-width: 600px) {
    /* Mobile optimizations */
    - Reduced padding
    - Smaller font sizes
    - Adjusted spacing
}
```

## Customization

### Changing Colors

Edit the CSS `:root` variables at the top of the template:

```css
:root {
    --ms-blue: #0078D4;        /* Primary brand color */
    --ms-green: #107C10;       /* Action items color */
    --ms-orange: #D83B01;      /* CTA color */
    /* ... other colors */
}
```

### Modifying Layout

Key layout parameters:

- **Max Width**: `680px` (email-safe width)
- **Padding**: `40px` (desktop), `20px` (mobile)
- **Border Radius**: `4px` (cards), `8px` (larger sections)
- **Spacing**: `32px` (section gaps), `20px` (card gaps)

### Adding Sections

To add new sections:

1. Add a placeholder in the template: `{{NEW_SECTION}}`
2. Create a builder method in `newsletter_generator.py`:
   ```python
   def _build_new_section(self, data):
       return f"<div class='new-section'>{data}</div>"
   ```
3. Replace the placeholder in `_generate_html_from_template()`

## Microsoft Design Principles Applied

1. **Clarity**: Clean hierarchy, generous whitespace
2. **Confidence**: Bold colors, clear typography
3. **Efficiency**: Scannable content, visual grouping
4. **Fluency**: Smooth transitions, subtle animations
5. **Accessibility**: High contrast, readable fonts

## Email Client Compatibility

The template is designed for:
- ✅ Modern web browsers (Chrome, Firefox, Safari, Edge)
- ✅ Outlook (web)
- ⚠️ Outlook (desktop) - May require additional testing
- ✅ Gmail
- ✅ Apple Mail

**Note**: For email distribution, consider using an email-specific template service or inline CSS tool.

## Example Output

When the generator processes content, it produces an HTML file that:
- Looks professional and modern
- Matches Microsoft's technical blog style
- Is fully responsive
- Contains all extracted knowledge in a structured format
- Can be opened directly in a browser or embedded in email

## Template Maintenance

### Version History
- **v1.0** (Nov 2025) - Initial Microsoft Fluent Design template

### Future Enhancements
- Dark mode support
- Additional color themes
- Print-optimized styles
- Email inline CSS version

## Support

For template issues or customization requests, refer to the main project documentation or modify the template file directly.

---

**Template Version**: 1.0  
**Design System**: Microsoft Fluent Design  
**Last Updated**: November 2025
