from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.datastructures import SortedDict
from django.utils.encoding import force_unicode


class ActionMixin(object):
    """
    allows the view to perform actions on list items
    This view expects `get_queryset` to be present
    """
    action_name = "action"
    selected_name = "selected"
    actions = ['delete_selected']
    delete_selected_template = "danemco/actions/delete_selected.html"

    # you can provide your own with a mixin or by extending your class
    def delete_selected(self, request, queryset):
        if "confirmed" in request.POST:
            for obj in queryset:
                # calling individual deletes so triggers will run
                obj.delete()
            return redirect(".")
        return render(request, self.delete_selected_template, {
            "selected_name": self.selected_name,
            "action_name": self.action_name,
            "action": request.REQUEST.get(self.action_name),
            "queryset": queryset,
        })
    delete_selected.short_description = "Delete selected %(verbose_name_plural)s"

    def get_actions(self):
        self.action_list = SortedDict()
        for action in self.actions:
            if callable(action):
                slug = action.__name__
                func = action
            elif hasattr(self, action):
                slug = action
                func = getattr(self, action)
            else:
                continue

            if hasattr(func, "short_description"):
                title = func.short_description % {
                    "verbose_name": force_unicode(self.model._meta.verbose_name),
                    "verbose_name_plural": force_unicode(self.model._meta.verbose_name_plural)
                }
            else:
                title = slug.title().replace("_", " ")

            self.action_list[slug] = (title, func)

        return self.action_list

    def get_context_data(self, **kwargs):

        print ("getting actions",)

        if not hasattr(self, "action_list"):
            self.action_list = self.get_actions()

        actions = [(k, a[0]) for k, a in self.action_list.items()]

        print (actions,)

        return super(ActionMixin, self).get_context_data(
            action_name=self.action_name,
            selected_name=self.selected_name,
            actions=actions,
            **kwargs)

    def perform_action(self, action):
        """
        Executes the given action and Returns None or an HttpResponse
        """
        self.action_list = self.get_actions()
        if action and action in self.action_list:
            title, func = self.action_list.get(action)
            ids = self.request.POST.getlist(self.selected_name)
            queryset = self.get_queryset().filter(id__in=ids)
            retval = func(self.request, queryset)
            if isinstance(retval, HttpResponse):
                return retval