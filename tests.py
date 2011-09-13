from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from magazine.models import Author, Issue, Article

class AuthorTestCase(TestCase):
    fixtures = ['test_authors.json',]

    def setUp(self):
        self.paul = Author.objects.get(pk = 1)
        self.dom  = Author.objects.get(pk = 2)

    def testUnicode(self):
        self.assertEqual(self.paul.__unicode__(), u'Paul Beasley-Murray')
        self.assertEqual(self.dom.__unicode__(), u'Dominic Rodger')

class IssueTestCase(TestCase):
    fixtures = ['test_issues.json',]

    def setUp(self):
        self.issue_1 = Issue.objects.get(pk = 1)
        self.issue_2 = Issue.objects.get(pk = 2)

    def testUnicode(self):
        self.assertEqual(self.issue_1.__unicode__(), u'Issue 1')
        self.assertEqual(self.issue_2.__unicode__(), u'Issue 3')

    def testMonthYear(self):
        self.assertEqual(self.issue_1.month_year(), u'January 2010')
        self.assertEqual(self.issue_2.month_year(), u'April 2010')

    def testDefaultPublished(self):
        self.assertEqual(self.issue_1.published, True)
        self.assertEqual(self.issue_2.published, True)

    def testCurrentIssue(self):
        self.assertEqual(Issue.current_issue(), self.issue_2)
        self.issue_2.published = False
        self.issue_2.save()

        self.assertEqual(Issue.current_issue(), self.issue_1)

        self.issue_2.published = True
        self.issue_2.save()

    def testGetURL(self):
        self.assertEqual(self.issue_1.get_absolute_url(), reverse('issue_detail', args=[self.issue_1.number,]))
        self.assertEqual(self.issue_2.get_absolute_url(), reverse('issue_detail', args=[self.issue_2.number,]))

class ArticleTestCase(TestCase):
    fixtures = ['test_issues.json', 'test_authors.json', 'test_articles.json',]

    def setUp(self):
        self.article_1 = Article.objects.get(pk = 1)
        self.article_2 = Article.objects.get(pk = 2)
        self.article_3 = Article.objects.get(pk = 3)

    def testUnicode(self):
        self.assertEqual(self.article_1.__unicode__(), u'My first article')
        self.assertEqual(self.article_2.__unicode__(), u'My second article')
        self.assertEqual(self.article_3.__unicode__(), u'My third article')

    def testMarkVisited(self):
        self.assertEqual(self.article_1.hits, 0)
        self.article_1.mark_visited()
        self.article_1 = Article.objects.get(pk = 1)
        self.assertEqual(self.article_1.hits, 1)
        self.article_1.mark_visited()
        self.article_1 = Article.objects.get(pk = 1)
        self.assertEqual(self.article_1.hits, 2)

    def testTeaser(self):
        self.assertEqual(self.article_1.teaser(), u'Witty description of the first article')
        self.assertEqual(self.article_2.teaser(), u'Full text of the second article. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate ...')
        self.assertEqual(self.article_3.teaser(), u'None available.')

    def testGetURL(self):
        self.assertEqual(self.article_1.get_absolute_url(), reverse('article_detail', args=[self.article_1.issue.number, self.article_1.pk,]))
        self.assertEqual(self.article_2.get_absolute_url(), reverse('article_detail', args=[self.article_2.issue.number, self.article_2.pk,]))

class MagazineGeneralViewsTestCase(TestCase):
    fixtures = ['test_issues.json', 'test_authors.json', 'test_articles.json',]

    def setUp(self):
        self.article_1 = Article.objects.get(pk = 1)
        self.article_2 = Article.objects.get(pk = 2)
        self.article_3 = Article.objects.get(pk = 3)
        self.issue_1 = Issue.objects.get(pk = 1)
        self.issue_2 = Issue.objects.get(pk = 2)
        self.issue_3 = Issue.objects.get(pk = 3)

        if not hasattr(self, 'staff_user'):
            self.staff_user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
            self.staff_user.is_staff = True
            self.staff_user.save()

        if not hasattr(self, 'user'):
            self.user = User.objects.create_user('ringo', 'starr@thebeatles.com', 'ringopassword')

    def testIndexView(self):
        response = self.client.get(reverse('magazine_index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['current_articles']), [self.article_3])
        self.assertEqual(response.context['current_issue'], self.issue_2)
        self.assertNotContains(response, self.article_1.teaser())
        self.assertNotContains(response, self.article_2.teaser())
        self.assertContains(response, self.article_3.teaser())

        self.issue_2.published = False
        self.issue_2.save()

        response = self.client.get(reverse('magazine_index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['current_articles']), [self.article_1, self.article_2])
        self.assertEqual(response.context['current_issue'], self.issue_1)
        self.assertContains(response, self.article_1.teaser())
        self.assertContains(response, self.article_2.teaser())
        self.assertNotContains(response, self.article_3.teaser())

        self.issue_2.published = True
        self.issue_2.save()

    def testIssueDetailView(self):
        response = self.client.get(reverse('issue_detail', args=[1]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['issue'], self.issue_1)

        # Check that trying to fetch an issue that isn't yet published
        # results in a 404
        response = self.client.get(reverse('issue_detail', args=[2]))
        self.assertEqual(response.status_code, 404)

        # ... still doesn't work if you login as a regular user
        self.client.login(username='ringo', password='ringopassword')
        response = self.client.get(reverse('issue_detail', args=[2]))
        self.assertEqual(response.status_code, 404)
        self.client.logout()

        # ... but does you're logged in as a staff member
        self.client.login(username='john', password='johnpassword')
        response = self.client.get(reverse('issue_detail', args=[2]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['issue'], self.issue_3)
        self.client.logout()

        response = self.client.get(reverse('issue_detail', args=[3]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['issue'], self.issue_2)

        response = self.client.get(reverse('issue_detail', args=[4]))
        self.assertEqual(response.status_code, 404)

    def testArticleDetailView(self):
        response = self.client.get(reverse('article_detail', args=[1, 1]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['issue'], self.issue_1)
        self.assertEqual(response.context['article'], self.article_1)
        self.assertContains(response, self.article_1.title)

        # Check that we've updated hit counts.
        self.assertEqual(Article.objects.get(pk = self.article_1.pk).hits, 1)
        response = self.client.get(reverse('article_detail', args=[1, 1]))
        self.assertEqual(Article.objects.get(pk = self.article_1.pk).hits, 2)

        # Check for fetching an article for an issue number where
        # the primary key and the issue number don't line up.
        response = self.client.get(reverse('article_detail', args=[3, 3]))
        self.assertEqual(response.status_code, 200)
        # Issue with pk 2 has number 3
        self.assertEqual(response.context['issue'], self.issue_2)
        self.assertEqual(response.context['article'], self.article_3)

        # Check that fetching an article by the wrong issue number
        # results in a 404.
        response = self.client.get(reverse('article_detail', args=[2, 2]))
        self.assertEqual(response.status_code, 404)

        # Check that fetching an article by a non-existent issue
        # number results in a 404.
        response = self.client.get(reverse('article_detail', args=[300, 2]))
        self.assertEqual(response.status_code, 404)

        # Check that fetching an article that doesn't exist
        # results in a 404.
        response = self.client.get(reverse('article_detail', args=[1, 200]))
        self.assertEqual(response.status_code, 404)

        # Check that fetching an article for an issue that
        # isn't yet published results in a 404.
        response = self.client.get(reverse('article_detail', args=[2, 4]))
        self.assertEqual(response.status_code, 404)

        # ... still doesn't work if you login as a regular user
        self.client.login(username='ringo', password='ringopassword')
        response = self.client.get(reverse('article_detail', args=[2, 4]))
        self.assertEqual(response.status_code, 404)
        self.client.logout()

        # ... but does if you're logged in as a staff member
        self.client.login(username='john', password='johnpassword')
        response = self.client.get(reverse('article_detail', args=[2, 4]))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

        # Check that the full text is rendered
        response = self.client.get(reverse('article_detail', args=[1, 2]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['issue'], self.issue_1)
        self.assertEqual(response.context['article'], self.article_2)
        self.assertContains(response, self.article_2.text)