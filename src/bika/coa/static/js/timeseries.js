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
        var absoluteMinY, all_values, avg_col, avg_columns, avg_key, c, col_colors, col_types, columns, curve_val, data, drawn_line_counter, drawn_lines, err_col, err_key, error, error_columns, headers, height, i, index, interp, legend, legendItems, line_configs, margin, maxError, maxY, minY, svg, svg_height, values, visible_cols, visible_idxs, visible_values, width, xScale, yScale, y_offset;
        try {
          // console.log("Data being used for rendering:", this.state.value)  # Log the data
          // console.log "TimeSeries::build_graph: entered"
          values = this.state.value;
          if (values === "") {
            console.log("TimeSeries::build_graph: exit because no data");
            this.container.current.appendChild([]);
            return;
          }
          // console.log 'Graph raw data: ' + values
          // Get datasets
          columns = this.props.item.time_series_columns;
          visible_cols = function () {
            var j, len, results;
            results = [];
            for (j = 0, len = columns.length; j < len; j++) {
              c = columns[j];
              if (c.ColumnHide !== 'on') {
                results.push(c);
              }
            }
            return results;
          }();
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
          // console.log 'Graph headers: ' + headers
          index = headers[0];
          err_col = "";
          err_key = "";
          error_columns = function () {
            var j, len, results;
            results = [];
            for (j = 0, len = columns.length; j < len; j++) {
              c = columns[j];
              if (c.ColumnType === 'errorbar') {
                results.push(c);
              }
            }
            return results;
          }();
          if (error_columns.length === 1) {
            err_col = error_columns[0];
            err_key = error_columns[0].ColumnTitle;
          }
          avg_col = "";
          avg_key = "";
          avg_columns = function () {
            var j, len, results;
            results = [];
            for (j = 0, len = columns.length; j < len; j++) {
              c = columns[j];
              if (c.ColumnType === 'average') {
                results.push(c);
              }
            }
            return results;
          }();
          if (avg_columns.length === 1) {
            avg_col = avg_columns[0];
            avg_key = avg_columns[0].ColumnTitle;
          }
          drawn_lines = function () {
            var j, len, results;
            results = [];
            for (i = j = 0, len = columns.length; j < len; i = ++j) {
              c = columns[i];
              if (c.ColumnHide !== 'on' && c.ColumnType !== 'errorbar') {
                results.push({
                  'idx': i,
                  'title': c.ColumnTitle,
                  'color': c.ColumnColor
                });
              }
            }
            return results;
          }().slice(1);
          visible_idxs = function () {
            var j, len, results;
            results = [];
            for (i = j = 0, len = columns.length; j < len; i = ++j) {
              c = columns[i];
              if (c.ColumnHide !== 'on') {
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
          // console.log 'visible_values: ' + JSON.stringify(visible_values)
          data = this.to_matrix(visible_values, headers, 'graph');
          // console.log 'data: ' + JSON.stringify(data)

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
          maxError = 0;
          if (err_key) {
            maxError = d3.max(data.flatMap(function (row) {
              return parseFloat(row[err_key]);
            }));
          }
          all_values = data.flatMap(function (row) {
            return drawn_lines.map(function (header) {
              return parseFloat(row[header['title']]);
            });
          });
          absoluteMinY = d3.min(all_values);
          absoluteMinY -= maxError;
          if (absoluteMinY === 0) {
            minY = -0.5;
          } else if (absoluteMinY > 0) {
            minY = absoluteMinY * 0.95;
          } else {
            minY = absoluteMinY * 1.05;
          }
          maxY = d3.max(all_values);
          maxY += maxError;
          // console.log('minY: ' + minY + ' maxY: ' + maxY + " height: " + height)
          yScale = d3.scaleLinear().domain([minY, maxY]).nice().range([height, 0]); // expands domain to "nice" human-friendly values
          // Create SVG container
          y_offset = 140;
          svg = d3.select(this.container).append('svg').attr("id", "timeseries-svg").style("height", "".concat(height + y_offset // Add unique ID
          , "px"));
          // Remove any previous SVG content
          svg.selectAll('*').remove();
          svg_height = height + margin.top + margin.bottom;
          // console.log('svg_height: ' + svg_height)
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
          drawn_line_counter = 0;
          headers.slice(1).forEach(function (key, i) {
            var capWidth, filteredData, lineGen, line_configs_idx, symbol;
            line_configs_idx = i % line_configs.length;
            // console.info "Main loop: " + key + "  " + i

            // Filter data to exclude rows with null, undefined, or non-numeric values for the current key
            filteredData = data.filter(function (d) {
              return d[index] != null && d[key] != null && d[index] !== "" && d[key] !== "" && !(typeof d[index] !== 'string' && (d[index] === null || isNaN(d[index]))) && !(typeof d[key] !== 'string' && (d[key] === null || isNaN(d[key])));
            });
            // console.log 'filteredData: ' + JSON.stringify(filteredData)

            // Line generator
            lineGen = d3.line().curve(curve_val).x(function (d) {
              return xScale(d[index]);
            }).y(function (d) {
              return yScale(d[key]);
            });
            if (key !== err_key) {
              svg.append("path").datum(filteredData).attr("fill", "none").attr("stroke-width", 2).attr("stroke", col_colors[i + 1]).attr("stroke-dasharray", line_configs[line_configs_idx].dash).attr("d", lineGen); // Use filtered data
              symbol = line_configs[line_configs_idx].symbol;
              // Add data points with different symbols
              svg.selectAll(".symbol-".concat(i)).data(filteredData).enter().append("path").attr("class", "symbol symbol-".concat(i // Use filtered data
              )).attr("d", symbolGenerator.type(symbol)).attr("transform", function (d) {
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
              drawn_lines[drawn_line_counter]['symbol'] = symbol;
              return drawn_line_counter += 1;
            } else {
              svg.selectAll(".error-bar").data(filteredData).enter().append("line").attr("class", "error-bar").attr("x1", function (d) {
                return xScale(d[index]);
              }).attr("x2", function (d) {
                return xScale(d[index]);
              }).attr("y1", function (d) {
                return yScale(d[avg_key] - d[err_key]);
              }).attr("y2", function (d) {
                return yScale(d[avg_key] + d[err_key]);
              }).attr("stroke", avg_col.ColumnColor).attr("stroke-width", 1);
              // Caps
              capWidth = 0.5;
              // Top cap
              svg.selectAll(".error-cap-top").data(filteredData).enter().append("line").attr("class", "error-cap-top").attr("x1", function (d) {
                return xScale(d[index] - capWidth / 2);
              }).attr("x2", function (d) {
                return xScale(d[index] + capWidth / 2);
              }).attr("y1", function (d) {
                return yScale(d[avg_key] + d[err_key]);
              }).attr("y2", function (d) {
                return yScale(d[avg_key] + d[err_key]);
              }).attr("stroke", avg_col.ColumnColor).attr("stroke-width", 1);
              // Bottom cap
              return svg.selectAll(".error-cap-bottom").data(filteredData).enter().append("line").attr("class", "error-cap-bottom").attr("x1", function (d) {
                return xScale(d[index] - capWidth / 2);
              }).attr("x2", function (d) {
                return xScale(d[index] + capWidth / 2);
              }).attr("y1", function (d) {
                return yScale(d[avg_key] - d[err_key]);
              }).attr("y2", function (d) {
                return yScale(d[avg_key] - d[err_key]);
              }).attr("stroke", avg_col.ColumnColor).attr("stroke-width", 1);
            }
          });
          // Add legend
          legend = svg.append("g").attr("class", "legend").attr("transform", "translate(50, ".concat(height + 50, ")"));

          // Add legend items
          legendItems = legend.selectAll("g").data(drawn_lines).enter().append("g").attr("transform", function (d, i) {
            var xOffset, yOffset;
            xOffset = parseFloat(i % Math.floor(width / 100) * 100); // Horizontal spacing
            yOffset = parseFloat(Math.floor(i / Math.floor(width / 100)) * 20); // Vertical spacing
            return "translate(".concat(xOffset, ", ").concat(yOffset, ")");
          });
          // Add legend color symbols
          legendItems.append("path").attr("d", function (d, i) {
            console.log('d: ' + d);
            return d3.symbol().type(d['symbol']).size(100)();
          }).attr("transform", "translate(9, 9)").style("fill", function (d, i) {
            // Center the symbol within the legend item
            return d['color'];
          });
          // Add legend text
          legendItems.append("text").attr("x", 24).attr("y", 9).attr("dy", "0.35em").style("font-size", "12px").text(function (d) {
            return d['title'];
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