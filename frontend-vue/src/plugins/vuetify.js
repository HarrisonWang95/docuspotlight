import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        dark: false,
        colors: {
          primary: '#1976d2',
          secondary: '#0288d1',
          accent: '#03a9f4',
          error: '#f44336',
          warning: '#ff9800',
          info: '#00bcd4',
          success: '#4caf50',
          background: '#f0f4f8'
        }
      }
    }
  }
})

export default vuetify