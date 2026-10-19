/* Load a height map through Gwyddion's own file modules (libgwyapp +
 * libgwymodule) and print what Gwyddion's libprocess computes for it.
 * Output is KEY=VALUE lines parsed by smoke_gwyddion.py.            */
#include <stdio.h>
#include <libgwyddion/gwyddion.h>
#include <libprocess/gwyprocess.h>
#include <libgwymodule/gwymodule.h>
#include <libdraw/gwydraw.h>
#include <app/gwyapp.h>

int main(int argc, char **argv)
{
    GError *err = NULL;
    GwyContainer *data;
    GwyDataField *field;
    GQuark key;

    if (argc != 2) { fprintf(stderr, "usage: %s FILE\n", argv[0]); return 2; }
    /* Headless init, as gwyddion-thumbnailer does: no GTK display needed,
     * only the type system and the file-format modules. */
    {
        gchar **dirs = gwy_app_settings_get_module_dirs();
        gchar *filedirs[8] = { NULL };
        guint i, n = 0;
        gwy_process_type_init();
        gwy_draw_type_init();
        gwy_resource_class_load(g_type_class_peek(GWY_TYPE_GRADIENT));
        gwy_resource_class_load(g_type_class_peek(GWY_TYPE_GL_MATERIAL));
        for (i = 0; dirs[i] && n < 7; i++)
            if (g_str_has_suffix(dirs[i], G_DIR_SEPARATOR_S "file"))
                filedirs[n++] = g_strdup(dirs[i]);
        gwy_module_register_modules((const gchar **)filedirs);
        if (!n) {
            fprintf(stderr, "no Gwyddion file-module directory found\n");
            return 3;
        }
    }
    printf("GWY_VERSION=%s\n", gwy_version_string());
    data = gwy_file_load(argv[1], GWY_RUN_NONINTERACTIVE, &err);
    if (!data) {
        fprintf(stderr, "load failed: %s\n", err ? err->message : "?");
        return 4;
    }
    printf("DETECTED_MODULE=%s\n", gwy_file_detect(argv[1], FALSE, GWY_FILE_OPERATION_LOAD));
    key = gwy_app_get_data_key_for_id(0);
    if (!gwy_container_gis_object(data, key, &field)) {
        fprintf(stderr, "no channel 0 in file\n");
        return 5;
    }
    printf("XRES=%d\nYRES=%d\n", gwy_data_field_get_xres(field), gwy_data_field_get_yres(field));
    printf("XREAL=%.9g\nYREAL=%.9g\n", gwy_data_field_get_xreal(field), gwy_data_field_get_yreal(field));
    printf("MEAN=%.9g\nRMS=%.9g\n", gwy_data_field_get_avg(field), gwy_data_field_get_rms(field));
    printf("MIN=%.9g\nMAX=%.9g\n", gwy_data_field_get_min(field), gwy_data_field_get_max(field));
    return 0;
}
