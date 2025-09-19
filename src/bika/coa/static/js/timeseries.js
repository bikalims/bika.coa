/******/ (() => { // webpackBootstrap
/******/ 	"use strict";


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
     * Converts the string value to an array
     */
    return _createClass(TimeSeries, [{
      key: "to_matrix",
      value: function to_matrix(list, headers) {
        var matrix;
        // No values yet
        if (list.length === 0) {
          return [];
        }
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
        var absoluteMinY, col_colors, col_types, columns, curve_val, data, error, h, headers, height, i, index, interp, legend, legendItems, line_configs, margin, maxY, minY, svg, svg_height, values, visible_cols, visible_idxs, visible_values, width, xScale, yScale, y_offset;
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
          visible_cols = columns.filter(function (i) {
            return i.ColumnHide !== 'on';
          });
          if (visible_cols.length === 0) {
            return;
          }
          col_types = visible_cols.map(function (i) {
            return i.ColumnType;
          });
          col_colors = visible_cols.map(function (i) {
            return i.ColumnColor;
          });
          headers = visible_cols.map(function (i) {
            return i.ColumnTitle;
          });
          index = headers[0];
          visible_idxs = function () {
            var j, len, results;
            results = [];
            for (i = j = 0, len = columns.length; j < len; i = ++j) {
              h = columns[i];
              if (h.ColumnHide !== 'on') {
                results.push(i);
              }
            }
            return results;
          }();
          visible_values = values.map(function (row) {
            var j, len, results;
            results = [];
            for (j = 0, len = visible_idxs.length; j < len; j++) {
              i = visible_idxs[j];
              results.push(row[i]);
            }
            return results;
          });
          data = this.to_matrix(visible_values, headers);
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
          xScale = d3.scaleLinear().domain(d3.extent(data, function (d) {
            return parseFloat(d[index]);
          })).range([0, width]);
          // Set up Y scale with trimmed domain
          absoluteMinY = d3.min(data.flatMap(function (row) {
            return headers.slice(1).map(function (header) {
              return parseFloat(row[header]);
            });
          }));
          if (absoluteMinY > 0) {
            minY = absoluteMinY * 0.95;
          } else {
            minY = absoluteMinY * 1.05;
          }
          maxY = d3.max(data.flatMap(function (row) {
            return headers.slice(1).map(function (header) {
              return parseFloat(row[header]);
            });
          }));
          console.log('minY: ' + minY + ' maxY: ' + maxY + " height: " + height);
          yScale = d3.scaleLinear().domain([minY, maxY]).nice().range([height, 0]); // expands domain to "nice" human-friendly values
          // Create SVG container
          y_offset = 140;
          svg = d3.select(this.container).append('svg').attr("id", "timeseries-svg").style("height", "".concat(height + y_offset // Add unique ID
          , "px"));
          // Remove any previous SVG content
          svg.selectAll('*').remove();
          svg_height = height + margin.top + margin.bottom;
          console.log('svg_height: ' + svg_height);
          svg = svg.attr("width", width + margin.left + margin.right).attr("height", svg_height).attr('xmlns', 'http://www.w3.org/2000/svg').append("g").attr("transform", "translate(".concat(margin.left, ",").concat(margin.top, ")"));
          // Graph title
          svg.append("text").attr("x", width / 2).attr("y", -margin.top / 2).attr("text-anchor", "middle").style("font-size", "16px").style("font-weight", "bold").text(this.props.item.time_series_graph_title);
          // X-axis label
          svg.append("text").attr("x", width / 2).attr("y", height + margin.bottom - 10).attr("text-anchor", "middle").style("font-size", "12px").text(this.props.item.time_series_graph_xaxis);
          // Y-axis label
          svg.append("text").attr("transform", "rotate(-90)").attr("x", -height / 2).attr("y", -margin.left + 15).attr("text-anchor", "middle").style("font-size", "12px").text(this.props.item.time_series_graph_yaxis);
          // y-axis horizontal grid lines
          svg.append("g").attr("class", "grid horizontal").call(d3.axisLeft(yScale).tickSize(-width)).selectAll("line").style("stroke", "#999").style("stroke-dasharray", "2,2").style("opacity", 0.8); // Extend ticks across the chart width // Lighter gray // Adjust transparency

          // Add vertical grid lines
          // console.log('height: ' + height)
          svg.append("g").attr("class", "grid vertical").attr("transform", "translate(0, ".concat(height, ")")).call(d3.axisBottom(xScale).tickSize(-height)).selectAll("line").style("stroke", "#999").style("stroke-dasharray", "2,2").style("opacity", 0.8); // Extend ticks across the chart height // Lighter gray // Adjust transparency

          // Get interpolation
          interp = this.props.item.time_series_graph_interpolation;
          // console.log(interp)
          curve_val = d3[interp];
          headers.slice(1).forEach(function (key, i) {
            var lineGen, line_configs_idx, validData;
            line_configs_idx = i % line_configs.length;
            console.info("Main loop: " + key + "  " + i);
            // Filter data to exclude rows with null, undefined, or non-numeric values for the current key
            validData = data.filter(function (d) {
              return d[key] != null && !isNaN(d[key]);
            });
            // Line generator
            lineGen = d3.line().curve(curve_val).x(function (d) {
              return xScale(d[index]);
            }).y(function (d) {
              return yScale(d[key]);
            });
            svg.append("path").datum(validData).attr("fill", "none").attr("stroke-width", 2).attr("stroke", col_colors[i + 1]).attr("stroke-dasharray", line_configs[line_configs_idx].dash).attr("d", lineGen); // Use filtered data
            // Add data points with different symbols
            return svg.selectAll(".symbol-".concat(i)).data(validData).enter().append("path").attr("class", "symbol symbol-".concat(i // Use filtered data
            )).attr("d", symbolGenerator.type(line_configs[line_configs_idx].symbol)).attr("transform", function (d) {
              var xVal, yVal;
              // Ensure valid x and y before applying transform
              xVal = parseFloat(d[index]);
              yVal = parseFloat(d[key]);
              if (!isNaN(xVal) && !isNaN(yVal)) {
                return "translate(".concat(xScale(xVal), ", ").concat(yScale(yVal), ")");
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
            var line_configs_idx;
            line_configs_idx = i % line_configs.length;
            return d3.symbol().type(line_configs[line_configs_idx].symbol).size(100)();
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