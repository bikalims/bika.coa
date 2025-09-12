const path = require('path');
const staticPath = path.resolve(__dirname, "../src/bika/coa/static");

const devMode = process.env.mode == "development";
const prodMode = process.env.mode == "production";
const mode = process.env.mode;
console.log(`RUNNING WEBPACK IN '${mode}' MODE`);

module.exports = {
    mode: 'development', // or 'production'

    devtool: 'source-map',
    entry: './app/TimeSeries.coffee', // Entry point for your CoffeeScript file
    output: {
        filename: 'timeseries.js', // Output file name
        path: path.resolve(staticPath, 'js'), // Output directory
        publicPath: "++plone++bika.coa.static/js/timeseries.js"
    },
    optimization: {
        minimize: false, // Disable minimization
    },
    module: {
        rules: [
            {
                test: /\.coffee$/,
                use: {
                    loader: 'coffee-loader',
                    options: {
                        transpile: {
                            presets: ['@babel/preset-env', '@babel/preset-react'],
                        },
                    },
                },
            },
            {
                test: /\.jsx?$/, // For JavaScript/JSX files
                use: 'babel-loader',
                exclude: /node_modules/,
            },
        ],
    },
    resolve: {
        extensions: ['.coffee', '.js', '.jsx'], // Allow importing without specifying extensions
    },
};
