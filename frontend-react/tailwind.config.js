export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}"
  ],
  theme: {
    extend: {
      colors: {
        primary: '#667eea',
        secondary: '#764ba2',
        success: '#52c41a',
        danger: '#ff6b6b',
        warning: '#ffa94d',
        info: '#4dabf7',
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'gradient-warning': 'linear-gradient(135deg, #ffa94d 0%, #ff922b 100%)',
        'gradient-success': 'linear-gradient(135deg, #52c41a 0%, #51cf66 100%)',
      }
    }
  },
  plugins: []
}
