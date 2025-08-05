/******/ (() => { // webpackBootstrap
/******/ 	"use strict";
/*!*******************************!*\
  !*** ./app/TimeSeries.coffee ***!
  \*******************************/


function _typeof(o) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (o) { return typeof o; } : function (o) { return o && "function" == typeof Symbol && o.constructor === Symbol && o !== Symbol.prototype ? "symbol" : typeof o; }, _typeof(o); }
function _classCallCheck(a, n) { if (!(a instanceof n)) throw new TypeError("Cannot call a class as a function"); }
function _defineProperties(e, r) { for (var t = 0; t < r.length; t++) { var o = r[t]; o.enumerable = o.enumerable || !1, o.configurable = !0, "value" in o && (o.writable = !0), Object.defineProperty(e, _toPropertyKey(o.key), o); } }
function _createClass(e, r, t) { return r && _defineProperties(e.prototype, r), t && _defineProperties(e, t), Object.defineProperty(e, "prototype", { writable: !1 }), e; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == _typeof(i) ? i : i + ""; }
function _toPrimitive(t, r) { if ("object" != _typeof(t) || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r || "default"); if ("object" != _typeof(i)) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }
var TimeSeries;
window.d3 = d3;
TimeSeries = function () {
  var getLineConfigs, symbolGenerator;
  var TimeSeries = /*#__PURE__*/function () {
    /**
     * TimeSeries Field for the Listing Table
     *
     * A multi value field is identified by the column type "timeseries" in the
     * listing view, e.g.  `self.columns = {"Result": {"type": "timeseries"}, ... }`
     *
     */
    function TimeSeries(config) {
      _classCallCheck(this, TimeSeries);
      this.container = config.container; // DOM element
      this.state = config.state;
      this.props = config.props;
    }

    // console.log('constructor complete')
    /*
     * Calculate Y range
     */
    return _createClass(TimeSeries, [{
      key: "get_Y_range",
      value: function get_Y_range(minY, maxY) {
        var diffY, interval, maxTicks, minTicks, y_range;
        diffY = maxY - minY;
        interval = 0;
        if (diffY > 70) {
          interval = 10;
        } else if (diffY > 50) {
          interval = 5;
        } else if (diffY > 20) {
          interval = 2;
        } else if (diffY > 10) {
          interval = 1;
        }
        if (interval > 0) {
          minTicks = minY - minY % interval + interval;
          maxTicks = maxY + maxY % interval + interval;
          y_range = d3.range(minTicks, maxTicks, interval);
        } else {
          y_range = d3.range(minY, maxY);
        }
        // console.log "Y Axis: min: ", minY, " max: ", maxY, " diffY: ", diffY, " interval: ", interval
        return y_range;
      }

      /*
       * Converts the string value to an array
       */
    }, {
      key: "to_matrix",
      value: function to_matrix(listString, headers) {
        var list, matrix;
        if (!listString || listString.length === 0) {
          return [];
        }
        // Parse the string version of the list of lists into an array
        // list = JSON.parse(listString)
        list = listString;
        // Map each inner list to an object using the headers
        matrix = list.map(function (innerList) {
          var obj;
          obj = {};
          headers.forEach(function (header, index) {
            return obj[header] = innerList[index];
          });
          return obj;
        });
        matrix.map(function (row) {
          return headers.forEach(function (header, index) {
            if (index = 0) {
              return row[header] = row[header];
            } else {
              return row[header] = parseFloat(row[header]);
            }
          });
        });
        return matrix;
      }

      /*
       * Inputs table builder. Generates a table of  inputs as matrix
       */
    }, {
      key: "build_graph",
      value: function build_graph() {
        var absoluteMinY, col_colors, col_types, columns, curve_val, data, error, headers, height, index, interp, legend, legendItems, line_configs, margin, maxY, minY, minY_factor, svg, values, width, x, y, yAxis, y_range;
        try {
          // console.log("Data being used for rendering:", this.state.value)  # Log the data
          // console.log "TimeSeries::build_graph: entered"
          values = this.state.value;
          if (values === "") {
            console.log("TimeSeries::build_graph: exit because no data");
            this.container.current.appendChild([]);
            return;
          }
          // Get datasets
          columns = this.props.item.time_series_columns;
          col_types = columns.map(function (i) {
            return i.ColumnType;
          });
          col_colors = columns.map(function (i) {
            return i.ColumnColor;
          });
          headers = columns.map(function (i) {
            return i.ColumnTitle;
          });
          index = headers[0];
          data = this.to_matrix(values, headers);
          // Generate the line colors (exclude index)
          line_configs = getLineConfigs(headers.length - 1);
          // Set up dimensions
          margin = {
            top: 40,
            right: 80,
            bottom: 50,
            left: 60
          };
          width = 700 - margin.left - margin.right;
          height = 400 - margin.top - margin.bottom + 50;
          // Set up scales
          x = d3.scaleLinear().domain(d3.extent(data, function (d) {
            return parseFloat(d[index]);
          })).range([0, width]);
          // Set up Y scale with trimmed domain
          absoluteMinY = d3.min(data.flatMap(function (row) {
            return headers.slice(1).map(function (header) {
              return parseFloat(row[header]);
            });
          }));
          minY_factor = 0.05;
          minY = absoluteMinY - absoluteMinY * minY_factor;
          maxY = d3.max(data.flatMap(function (row) {
            return headers.slice(1).map(function (header) {
              return parseFloat(row[header]);
            });
          }));
          y = d3.scaleLinear().domain([Math.floor(minY), Math.ceil(maxY) // Trim domain to just cover data range
          ]).range([height, 0]);
          // Create SVG container
          svg = d3.select(this.container).append('svg').attr("id", "timeseries-svg").style("height", "".concat(height + 140 // Add unique ID
          , "px"));
          // Remove any previous SVG content
          svg.selectAll('*').remove();
          svg = svg.attr("width", width + margin.left + margin.right).attr("height", height + margin.top + margin.bottom).attr('xmlns', 'http://www.w3.org/2000/svg').append("g").attr("transform", "translate(".concat(margin.left, ",").concat(margin.top, ")"));
          // Graph title
          svg.append("text").attr("x", width / 2).attr("y", -margin.top / 2).attr("text-anchor", "middle").style("font-size", "16px").style("font-weight", "bold").text(this.props.item.time_series_graph_title);
          // X-axis
          svg.append("g").attr("transform", "translate(0,".concat(height, ")")).call(d3.axisBottom(x));
          // X-axis label
          svg.append("text").attr("x", width / 2).attr("y", height + margin.bottom - 10).attr("text-anchor", "middle").style("font-size", "12px").text(this.props.item.time_series_graph_xaxis);
          // Y-axis
          y_range = this.get_Y_range(minY, maxY);
          yAxis = d3.axisLeft(y).tickValues(y_range).tickSize(-width); // Extend ticks across the chart width

          // Y-axis label
          svg.append("text").attr("transform", "rotate(-90)").attr("x", -height / 2).attr("y", -margin.left + 15).attr("text-anchor", "middle").style("font-size", "12px").text(this.props.item.time_series_graph_yaxis);
          // Add horizontal grid lines
          svg.append("g").attr("class", "grid horizontal").attr("transform", "translate(0, 0)").call(yAxis).selectAll("line").style("stroke", "#999").style("opacity", 0.4); // Lighter gray // Adjust transparency

          // Add vertical grid lines
          svg.append("g").attr("class", "grid vertical").attr("transform", "translate(0, ".concat(height, ")")).call(d3.axisBottom(x).tickSize(-height).tickFormat("")).selectAll("line").style("stroke", "#999").style("stroke-dasharray", "2,2").style("opacity", 0.8); // Extend ticks across the chart height // Remove tick labels // Lighter gray // Adjust transparency

          // Draw axes
          svg.append("g").attr("transform", "translate(0,".concat(height, ")")).call(d3.axisBottom(x));
          // Get interpolation
          interp = this.props.item.time_series_graph_interpolation;
          // console.log(interp)
          curve_val = d3[interp];
          headers.slice(1).forEach(function (key, i) {
            var lineGen, validData;
            // console.debug "Main loop: " + key + "  " + i

            // Filter data to exclude rows with null, undefined, or non-numeric values for the current key
            validData = data.filter(function (d) {
              return d[key] != null && !isNaN(d[key]);
            });
            // Line generator
            lineGen = d3.line().curve(curve_val).x(function (d) {
              return x(d[index]);
            }).y(function (d) {
              return y(d[key]);
            });
            svg.append("path").datum(validData).attr("fill", "none").attr("stroke-width", 2).attr("stroke", col_colors[i + 1]).attr("stroke-dasharray", line_configs[i].dash).attr("d", lineGen); // Use filtered data
            // Add data points with different symbols
            return svg.selectAll(".symbol-".concat(i)).data(validData).enter().append("path").attr("class", "symbol symbol-".concat(i // Use filtered data
            )).attr("d", symbolGenerator.type(line_configs[i].symbol)).attr("transform", function (d) {
              var xVal, yVal;
              // Ensure valid x and y before applying transform
              xVal = parseFloat(d[index]);
              yVal = parseFloat(d[key]);
              if (!isNaN(xVal) && !isNaN(yVal)) {
                return "translate(".concat(x(xVal), ", ").concat(y(yVal), ")");
              } else {
                return null; // Skip invalid points
              }
            }).style("fill", col_colors[i + 1]);
          });
          // Add legend
          legend = svg.append("g").attr("class", "legend").attr("transform", "translate(50, ".concat(height + 50, ")"));

          // Add legend items
          legendItems = legend.selectAll("g").data(headers.slice(1)).enter().append("g").attr("transform", function (d, i) {
            var xOffset, yOffset;
            xOffset = parseFloat(i % Math.floor(width / 100) * 100); // Horizontal spacing
            yOffset = parseFloat(Math.floor(i / Math.floor(width / 100)) * 20); // Vertical spacing
            return "translate(".concat(xOffset, ", ").concat(yOffset, ")");
          });
          // Add legend color symbols
          legendItems.append("path").attr("d", function (d, i) {
            return d3.symbol().type(line_configs[i].symbol).size(100)();
          }).attr("transform", "translate(9, 9)").style("fill", function (d, i) {
            // Center the symbol within the legend item
            return col_colors[i + 1];
          });
          // Add legend text
          legendItems.append("text").attr("x", 24).attr("y", 9).attr("dy", "0.35em").style("font-size", "12px").text(function (d) {
            return d;
          });
          return console.log("TimeSeries::build_graph: ended");
        } catch (error1) {
          error = error1;
          return console.error("Error in build_graph:", error);
        }
      }
    }]);
  }();
  ;
  getLineConfigs = function getLineConfigs(count) {
    var configs;
    configs = [{
      symbol: d3.symbolStar,
      dash: ""
    }, {
      symbol: d3.symbolSquare,
      dash: ""
    }, {
      symbol: d3.symbolTriangle,
      dash: ""
    }, {
      symbol: d3.symbolDiamond,
      dash: ""
    }, {
      symbol: d3.symbolCross,
      dash: ""
    }];
    return configs.slice(0, count);
  };

  // Create symbol generator
  symbolGenerator = d3.symbol().size(48); // Adjust size as needed

  return TimeSeries;
}.call(void 0);
window.TimeSeries = TimeSeries;
/******/ })()
;
//# sourceMappingURL=timeseries.js.map