import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Item } from '../../models/item.model';
import { ItemService } from '../../services/item.service';

@Component({
  selector: 'app-item-detail',
  templateUrl: './item-detail.component.html',
  styleUrls: ['./item-detail.component.css']
})
export class ItemDetailComponent implements OnInit {
  item: Item | null = null;
  loading = false;
  error: string | null = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private itemService: ItemService
  ) { }

  ngOnInit() {
    this.getItem();
  }

  getItem() {
    this.loading = true;
    this.error = null;
    
    const id = Number(this.route.snapshot.paramMap.get('id'));
    
    this.itemService.getItem(id).subscribe({
      next: (data) => {
        this.item = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load item details. Please try again later.';
        this.loading = false;
        console.error('Error loading item:', err);
      }
    });
  }

  goBack() {
    this.router.navigate(['/items']);
  }
}
