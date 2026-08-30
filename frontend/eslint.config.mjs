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
  {
    files: ['src/components/PixelBlast.tsx'],
    rules: {
      '@typescript-eslint/ban-ts-comment': 'off',
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },
]

export default eslintConfig
