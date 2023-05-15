module.exports = {
  content: [
    "./src/**/*.tsx"
  ],
  theme: {
    minWidth: {
      '96': '96px'
    },
    extend: {},
  },
  darkMode: 'class', // or 'media' or 'class
  variants: {
    extend: {
      'backgroundColor': ['disabled']
    },
  },
  safelist: [
    'text-orange-500',
    'text-green-500',
    'text-blue-500',
    'text-red-500',
    {
      pattern: /text-([a-z]+)-(500)/,
    }
  ],
  plugins: [],
}
