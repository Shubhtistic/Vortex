import nextVitals from 'eslint-config-next/core-web-vitals'
import nextTypescript from 'eslint-config-next/typescript'

const eslintConfig = [
  {
    ignores: [
      '.next/**',
      'node_modules/**',
      'dist/**',
      'out/**',
      'build/**',
      'public/**',
      '.agents/**',
    ],
  },
  ...nextVitals,
  ...nextTypescript,

]

export default eslintConfig
