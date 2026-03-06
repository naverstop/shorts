module.exports = {
  presets: ['module:@react-native/babel-preset'],
  plugins: [
    [
      'module-resolver',
      {
        root: ['./src'],
        extensions: ['.ios.js', '.android.js', '.js', '.ts', '.tsx', '.json'],
        alias: {
          '@': './src',
          '@screens': './src/screens',
          '@services': './src/services',
          '@components': './src/components',
          '@types': './src/types',
          '@constants': './src/constants',
        },
      },
    ],
  ],
};
