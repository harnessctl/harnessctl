import templEslintConfig from '@templ-project/eslint';

export default [
  {
    ignores: [
      '**/*.config.cjs',
      '**/*.config.js',
      '**/*.config.mjs',
      '.eslintignore',
      '.gitignore',
      '.jscpd/**',
      '.prettierignore',
      '.venv/**',
      '.specs/**',
      'coverage/**',
      'dist/**',
      'docs-html/**',
      'jsconfig.json',
      'LICENSE',
      'node_modules/**',
      'package-lock.json',
      'package.json',
      'tsconfig.json',
    ],
  },
  ...templEslintConfig,
];
