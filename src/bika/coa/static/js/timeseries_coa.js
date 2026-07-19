// console.log('timeseries_coa start');

function get_time_series_config(element) {

      let columns = element.getAttribute('data-columns');
      let graph_interpolation = element.getAttribute('data-graph_interpolation');
      let graph_title = element.getAttribute('data-graph_title');
      let graph_xaxis = element.getAttribute('data-graph_xaxis');
      let graph_yaxis = element.getAttribute('data-graph_yaxis');
      let results = element.getAttribute('data-results');
      
      // console.log('Results: ' + results)
      try {
        columns = JSON.parse(columns);
        results = JSON.parse(results);
      } catch (e) {
        console.error("JSON parsing error:", e);
      }
      
      // Prep results
      new_results = []
      for (let i = 0; i < results.length; i++) {
        row = results[i];
        new_row = []
        for (let j = 0; j < row.length; j++) {
          item = row[j];
          val = item['val'];
          new_row.push(val);
        };
        new_results.push(new_row);
      }
      // console.log('NewResults: ' + new_results)
      
      // Create config for TimeSeries
      return {
        container: element,  // Pass the DOM element directly
        state: { value: new_results },
        props: {
          item: {
            time_series_columns: columns,
            time_series_graph_interpolation: graph_interpolation,
            time_series_graph_title: graph_title,
            time_series_graph_xaxis: graph_xaxis,
            time_series_graph_yaxis: graph_yaxis,
          }
        }
      }; 
}

function renderChart(el) {
  const config = get_time_series_config(el);
  const ts = new TimeSeries(config);

  try {
    const container = d3.select(el);
    container.selectAll("svg").remove();  // Clear existing SVGs
    container.selectAll("object").remove();

    // Keep the generated SVG inline. Impress/PDF rendering cannot reliably
    // wait for an SVG converted to an asynchronously loaded data-URL object.
    ts.build_graph();

  } catch (e) {
    console.error("Graph build failed:", e);
  }
};

// console.log('timeseries_coa loaded');
