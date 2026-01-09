/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // Premium Light Theme Palette
                'primary-bg': '#FAFAFA',
                'secondary-bg': '#FFFFFF',
                'accent-blue': '#2563EB',
                'text-main': '#1F2937',
                'text-heading': '#111827',
                'text-secondary': '#6B7280',
            },
            fontFamily: {
                sans: ['"Plus Jakarta Sans"', 'sans-serif'],
                heading: ['"Outfit"', 'sans-serif'],
            },
            boxShadow: {
                'soft': '0 4px 20px -2px rgba(0, 0, 0, 0.05)',
                'glow': '0 0 15px rgba(37, 99, 235, 0.3)',
            },
            backdropBlur: {
                'xs': '2px',
            }
        },
    },
    plugins: [],
}
