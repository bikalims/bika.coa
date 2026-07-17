/** COA Remarks interpretation-template selector. */
jQuery(function($) {
  $(".arinterpretationtemplates-selector[data-target='#COARemarks']").each(
    function() {
      var selector = $(this);
      var field = $("#archetypes-fieldname-COARemarks");
      var widget = field.find(".mce-tinymce, textarea#COARemarks").first();

      if (widget.length) {
        widget.before(selector);
      } else if (field.length) {
        field.append(selector);
      }

      selector.find("#interpretationtemplate-insert")
        .off("click.bika-coa")
        .on("click.bika-coa", function(event) {
          event.preventDefault();

          var template_uid = selector.find("#interpretationtemplate").val();
          if (!template_uid) return;

          var container = $(selector.data("target"));
          if (container.length !== 1) return;

          var editor = tinymce.get(container.attr("id"));
          if (!editor) return;

          var request_data = {
            catalog_name: "uid_catalog",
            UID: template_uid,
            include_fields: ["text"]
          };

          window.senaite.core.globals.jsonapi_read(
            request_data,
            function(data) {
              if (data.objects.length === 1) {
                editor.insertContent(data.objects[0].text);
              }
            }
          );
        });
    }
  );
});
