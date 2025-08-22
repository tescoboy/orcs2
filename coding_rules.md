# Coding Rules & Standards

## File Size Rule
- **STRICT RULE**: All files must be under 150 lines
- Break down large files into smaller, focused modules
- Each file should have a single responsibility
- Use imports to organize functionality across multiple files

## Code Quality Standards
- Write simple, easy-to-understand code
- Use clear, descriptive function and variable names
- Keep functions small and focused on one task
- Add comments for complex logic
- Follow consistent indentation and formatting

## CSS & Styling Rules
- **Use Bootstrap CSS exclusively** for all styling
- **NO inline CSS ever** - all styles must be in external CSS files
- Create clean, well-aligned layouts using Bootstrap's grid system
- Use Bootstrap utility classes for spacing, colors, and typography
- Custom styles should be in separate CSS files, not inline

## Bootstrap Usage Examples
```html
<!-- Good: Using Bootstrap classes -->
<div class="container">
  <div class="row">
    <div class="col-md-6">
      <div class="card">
        <div class="card-body">
          <h5 class="card-title">Title</h5>
          <p class="card-text">Content</p>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Bad: Inline CSS -->
<div style="width: 100%; padding: 20px; background: #f0f0f0;">
  <h1 style="color: blue; font-size: 24px;">Title</h1>
</div>
```

## File Organization
- Keep related functionality together
- Use logical directory structure
- Separate concerns (HTML, CSS, JavaScript, backend logic)
- Create reusable components and utilities

## Git Deployment Rule
- **NEVER deploy to git unless explicitly instructed**
- Always ask for permission before pushing changes
- Use local development and testing first
- Document changes before requesting deployment

## Code Review Checklist
- [ ] File is under 150 lines
- [ ] No inline CSS used
- [ ] Bootstrap classes used for styling
- [ ] Code is simple and readable
- [ ] Functions are small and focused
- [ ] Proper error handling included
- [ ] Comments added where needed
- [ ] Consistent formatting applied

## Project Structure Guidelines
```
src/
├── components/     # Reusable UI components
├── styles/         # CSS files (Bootstrap + custom)
├── services/       # Business logic
├── utils/          # Utility functions
└── pages/          # Page-specific components
```

## Remember
- **150 lines maximum per file**
- **Bootstrap CSS only**
- **No inline CSS**
- **Simple, readable code**
- **Ask before git deployment**
